import time
import pytesseract
from PIL import Image
import mss
from merge_engine import MergeEngine

from storage_manager import StorageManager


class ScreenOCREngine:
    def __init__(self, class_title="Untitled_Class", capture_interval=2):
        """
        class_title: used for meeting folder name
        capture_interval: seconds between captures
        """
        self.capture_interval = capture_interval
        self.last_text = ""
        self.storage = StorageManager()
        self.storage.start_new_meeting(class_title)
        


    def capture_screen(self):
        with mss.mss() as sct:
            monitor = sct.monitors[1]  # full screen
            screenshot = sct.grab(monitor)
            img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
            return img

    def extract_text(self, image):
        gray = image.convert("L")
        text = pytesseract.image_to_string(gray)
        cleaned = self.clean_text(text)
        return cleaned

    def clean_text(self, text):
        lines = text.splitlines()
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            if len(line) < 3:
                continue
            cleaned_lines.append(line)

        return "\n".join(cleaned_lines)

    def diff_text(self, new_text):
        if not self.last_text:
            self.last_text = new_text
            return new_text

        new_lines = new_text.splitlines()
        old_lines = self.last_text.splitlines()

        diff = []
        for line in new_lines:
            if line not in old_lines:
                diff.append(line)

        self.last_text = new_text
        return "\n".join(diff)

    def start(self):
        print("Screen OCR Engine with Storage started. Press CTRL+C to stop.\n")

        while True:
            try:
                img = self.capture_screen()
                text = self.extract_text(img)
                diff = self.diff_text(text)

                if diff.strip():
                    timestamp = time.strftime("%H:%M:%S")
                    print(f"[{timestamp}] New Text Detected:\n{diff}\n")
                    self.storage.append_visual_text(diff)

                time.sleep(self.capture_interval)

            except KeyboardInterrupt:
                print("\nScreen OCR Engine stopped.")
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(2)


if __name__ == "__main__":
    # Change class title here for now
    engine = ScreenOCREngine(class_title="DBMS_Unit3", capture_interval=2)
    engine.start()
