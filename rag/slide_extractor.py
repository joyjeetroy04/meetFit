import os
import cv2
import pytesseract
import re
import sys

# Smart Tesseract Path Resolution
if sys.platform == "win32":
    win_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(win_path):
        pytesseract.pytesseract.tesseract_cmd = win_path
# On Mac/Linux, Tesseract is usually in the system PATH, so pytesseract handles it automatically.

class SlideExtractor:

    def __init__(self, meeting_dir: str):
        self.meeting_dir = meeting_dir
        self.slides_dir = os.path.join(meeting_dir, "slides")

    def _clean_text(self, text: str) -> str:
        """
        Clean OCR noise
        """
        text = re.sub(r"\s+", " ", text)
        text = text.replace("|", " ")
        return text.strip()

    def extract(self):
        results = []

        if not os.path.exists(self.slides_dir):
            return results

        print(f"[SlideExtractor] 🔍 Running OCR on slides in {os.path.basename(self.meeting_dir)}...")

        for file in sorted(os.listdir(self.slides_dir)):

            if not file.lower().endswith((".jpg", ".png")):
                continue

            image_path = os.path.join(self.slides_dir, file)

            try:
                image = cv2.imread(image_path)

                if image is None:
                    continue

                # 🔹 improve OCR readability
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                gray = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)[1]

                text = pytesseract.image_to_string(gray)
                text = self._clean_text(text)

                if not text:
                    continue

                # 🔹 try extracting timestamp from filename
                start_elapsed = 0.0
                try:
                    # Assumes format "slide_12345.jpg"
                    start_elapsed = float(file.split("_")[1].split(".")[0])
                except Exception:
                    pass

                # 🔥 FIX: Match the exact schema AskEngine and MergeEngine expect!
                results.append({
                    "text": f"Slide Content: {text}",     # Prefix helps the LLM understand context
                    "source": "slide",
                    "image": file,                        # Pass just the filename for clean citation
                    "start_elapsed": start_elapsed,       # Engine uses this for sorting/seeking
                    "meeting": os.path.basename(self.meeting_dir) # Required for the prompt builder
                })
                
                print(f"  -> ✅ OCR successful: {file} ({len(text)} chars)")

            except Exception as e:
                print(f"  -> ❌ [SlideExtractor] OCR failed for {file}: {e}")

        return results