import os
import sounddevice as sd
import numpy as np
import whisper
import queue
import threading
import time
import wave
from typing import Optional, Dict, Any, cast

from storage_manager import StorageManager
from merge_engine import MergeEngine


def clean_academic_text(text: str) -> str:
    replacements = [
        " uh ", " um ", " okay so ", " so um ",
        " you know ", " kind of ", " sort of "
    ]
    lowered = text.lower()
    for r in replacements:
        lowered = lowered.replace(r, " ")
    return lowered.strip()


def resample_audio(audio_chunk: np.ndarray, orig_sr: int, target_sr: int = 16000) -> np.ndarray:
    """Dependency-free audio resampler using numpy linear interpolation."""
    if orig_sr == target_sr:
        return audio_chunk
    duration = len(audio_chunk) / orig_sr
    target_len = int(duration * target_sr)
    
    # Linear interpolation
    x_orig = np.linspace(0, duration, len(audio_chunk))
    x_target = np.linspace(0, duration, target_len)
    return np.interp(x_target, x_orig, audio_chunk).astype(np.float32)


class AudioSTTEngine:

    def __init__(
        self,
        storage: StorageManager,
        sample_rate: int = 16000,
        device_index: Optional[int] = None
    ):
        self.target_sample_rate = sample_rate # Whisper strictly needs 16000
        self.device_native_sr = sample_rate # Will be updated dynamically
        self.device_channels = 2 # Will be updated dynamically
        
        self.storage = storage
        self.device_index = device_index

        self.audio_queue: queue.Queue[Optional[np.ndarray]] = queue.Queue()
        self.model = whisper.load_model("base")

        self.running = False
        self.wav_writer = None
        self.session_start_time = None
        self.stream = None

        self.meeting_dir = self.storage.get_meeting_dir()
        if not self.meeting_dir:
            raise RuntimeError("Meeting directory not initialized in UI")

        self.wav_path = os.path.join(self.meeting_dir, "audio_raw.wav")
        self.merge = MergeEngine(self.meeting_dir)

    # --------------------------------------------------
    # CALLBACK (KEEP LIGHT)
    # --------------------------------------------------

    def audio_callback(self, indata, frames, time_info, status):
        # We don't print status here to avoid spamming the terminal with underflow warnings
        if self.wav_writer is not None:
            pcm = np.int16(np.clip(indata, -1, 1) * 32767)
            self.wav_writer.writeframes(pcm.tobytes())

        self.audio_queue.put(indata.copy())

    # --------------------------------------------------
    # FIND REAL WASAPI LOOPBACK DEVICE
    # --------------------------------------------------

    def get_loopback_device(self):
        devices = cast(list[Dict[str, Any]], sd.query_devices())

        # 1. Look for Stereo Mix explicitly
        for i, dev in enumerate(devices):
            name = dev["name"].lower()
            if ("loopback" in name or "stereo mix" in name) and dev["max_input_channels"] > 0:
                print(f"[Audio] Loopback device found: {dev['name']}")
                return i

        # 2. Fallback to default microphone if no Stereo Mix is found
        default_in = sd.default.device[0]
        if default_in is not None:
             print(f"[Audio] Falling back to default input: {devices[default_in]['name']}")
             return default_in

        print("[Audio] No loopback or input device found")
        return None

    # --------------------------------------------------
    # START LISTENING
    # --------------------------------------------------

    def start_listening(self):
        print("\n[Audio] Starting system audio capture...\n")

        self.running = True
        self.session_start_time = time.time()

        loopback_device = self.get_loopback_device()

        # Dynamically set capabilities based on the hardware
        # Dynamically set capabilities based on the hardware
        if loopback_device is not None:
            # Tell Pylance this is definitely a Dictionary to clear the warnings
            device_info = cast(Dict[str, Any], sd.query_devices(loopback_device))
            
            self.device_native_sr = int(device_info['default_samplerate'])
            self.device_channels = min(2, int(device_info['max_input_channels']))
        else:
            self.device_native_sr = 16000
            self.device_channels = 1

        print(f"[Audio] Hardware Native Setup: {self.device_native_sr}Hz | {self.device_channels} Channels")

        # Prepare WAV (Save at native hardware quality for the final refinement pass)
        self.wav_writer = wave.open(self.wav_path, "wb")
        self.wav_writer.setnchannels(self.device_channels)
        self.wav_writer.setsampwidth(2)
        self.wav_writer.setframerate(self.device_native_sr)

        # ------------------------
        # TRANSCRIPTION THREAD
        # ------------------------
        def transcribe_loop():
            buffer = np.zeros((0,), dtype=np.float32)
            
            # Whisper likes ~3 second chunks
            chunk_duration = 3 
            target_buffer_len = self.target_sample_rate * chunk_duration

            while self.running:
                try:
                    data = self.audio_queue.get(timeout=1)
                    if data is None:
                        break

                    # 1. Convert to mono if it's stereo
                    if self.device_channels > 1:
                        audio_chunk = np.mean(data, axis=1)
                    else:
                        audio_chunk = data[:, 0]

                    # 2. Resample to 16000Hz dynamically for Whisper
                    audio_chunk = resample_audio(audio_chunk, self.device_native_sr, self.target_sample_rate)
                    
                    buffer = np.concatenate((buffer, audio_chunk))

                    if len(buffer) >= target_buffer_len:
                        chunk = buffer[:target_buffer_len]
                        buffer = buffer[target_buffer_len:]

                        result = self.model.transcribe(
                            chunk,
                            fp16=False,
                            language="en",
                            temperature=0.1,
                            condition_on_previous_text=False
                        )

                        raw_text = str(result.get("text", ""))
                        if not raw_text.strip():
                            continue

                        text = clean_academic_text(raw_text)

                        if text and self.storage.start_time is not None:
                            elapsed = time.time() - self.storage.start_time
                            timestamp = time.strftime("%H:%M:%S")

                            print(f"[{timestamp}] {text}\n")

                            self.storage.append_audio_text(text, elapsed_seconds=elapsed)
                            self.merge.add_entry(text, "audio", elapsed_seconds=elapsed)

                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"[Audio] Transcription error: {e}")

        threading.Thread(target=transcribe_loop, daemon=True).start()

        # ------------------------
        # OPEN STREAM SAFELY
        # ------------------------
        try:
            self.stream = sd.InputStream(
                samplerate=self.device_native_sr,
                device=loopback_device,
                channels=self.device_channels,
                dtype="float32",
                callback=self.audio_callback,
                blocksize=2048, # Increased blocksize slightly to prevent stuttering
            )
            self.stream.start()
        except Exception as e:
            print("\n[Audio] Failed to open system audio stream.")
            print(f"[Audio Error] {e}")

    # --------------------------------------------------
    # STOP
    # --------------------------------------------------

    def stop(self):
        self.running = False
        self.audio_queue.put(None)

        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception as e:
                print(f"[Audio] Stream close error: {e}")
            finally:
                self.stream = None

        if self.wav_writer:
            try:
                self.wav_writer.close()
                print("[Audio] WAV finalized.")
            except Exception as e:
                print(f"[Audio] WAV close error: {e}")
            finally:
                self.wav_writer = None
                
        print("[Audio] Engine stopped.")