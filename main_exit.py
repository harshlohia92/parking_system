import cv2
import pyttsx3
from detector import PlateDetector
from ocr_reader import LPROCR
from parking_logic import handle_exit
from normalize_plate import normalize_plate
from utils import draw_plate_box



PLATE_MODEL = "models/platebest.pt"
LPR_MODEL = "models/best.pt"
VIDEO_SOURCE = "/Users/harshlohia/Downloads/IMG_2894.jpg"

plate_detector = PlateDetector(PLATE_MODEL)
ocr_reader = LPROCR(LPR_MODEL)
speaker = pyttsx3.init()

cap = cv2.VideoCapture(VIDEO_SOURCE)
print("Exit gate started...")

last_seen = {}
FRAME_DEBOUNCE = 30
frame_idx = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    h, w = frame.shape[:2]

    try:
        detections = plate_detector.detect(frame)
    except Exception as e:
        print("Plate detector error:", e)
        detections = []

    for det in detections:
        x1, y1, x2, y2 = det["coords"]


        crop = frame[y1:y2, x1:x2]

        if crop is None or crop.size == 0:
            continue


        raw_text = ocr_reader.read_text(crop)

        if raw_text is None:
            print("BAD OCR → None")
            frame = draw_plate_box(frame, (x1, y1, x2, y2), "")
            continue


        plate_text = normalize_plate(raw_text)

        if not plate_text:
            print("BAD NORMALIZED →", raw_text)
            frame = draw_plate_box(frame, (x1, y1, x2, y2), raw_text)
            continue


        last = last_seen.get(plate_text, -999)
        if frame_idx - last <= FRAME_DEBOUNCE:
            frame = draw_plate_box(frame, (x1, y1, x2, y2), plate_text)
            continue
        last_seen[plate_text] = frame_idx


        res = handle_exit(plate_text)
        print("EXIT:", plate_text, res)

        if res.get("status") == "ok":
            slot = res.get("slot_released")
            if slot:
                cv2.putText(frame, f"SLOT FREE: {slot}", (50, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
                try:
                    speaker.say(f"Slot {slot} is now freed. Thank you.")
                    speaker.runAndWait()
                except:
                    pass

        frame = draw_plate_box(frame, (x1, y1, x2, y2), plate_text)

    cv2.imshow("Exit Gate", frame)
    if cv2.waitKey(1) == 27:
        break

    frame_idx += 1

cap.release()
cv2.destroyAllWindows()
