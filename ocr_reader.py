import easyocr
import cv2
import numpy as np


class LPROCR:
    def __init__(self, model_path=None):
        self.reader = easyocr.Reader(['en'])

    def read_text(self, plate_crop):
        try:
            if plate_crop is None or plate_crop.size == 0:
                return None

            height, width = plate_crop.shape[:2]
            if width < 50 or height < 20:
                return None


            resized = cv2.resize(plate_crop, (300, 100), interpolation=cv2.INTER_CUBIC)


            gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (3, 3), 0)


            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)


            kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
            sharpened = cv2.filter2D(enhanced, -1, kernel)


            results = self.reader.readtext(sharpened, detail=1)
            if not results:
                return None


            results.sort(key=lambda x: x[0][0][1])


            text = ' '.join([res[1] for res in results if res[2] > 0.2])
            return text.strip().upper() if text else None
        except Exception as e:
            print(f"OCR Error: {e}")
            return None
