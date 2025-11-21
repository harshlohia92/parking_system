import cv2
import pyttsx3
from detector import PlateDetector
from vehicle_detector import VehicleDetector
from vehicle_map import VEHICLE_CLASSES
from ocr_reader import LPROCR
from parking_logic import handle_entry
from normalize_plate import normalize_plate
from utils import draw_plate_box

PLATE_MODEL = "models/platebest.pt"
VEHICLE_MODEL = "models/best.pt"
VIDEO_SOURCE = "/Users/harshlohia/Downloads/IMG_2895.jpg"

plate_detector = PlateDetector(PLATE_MODEL)
vehicle_detector = VehicleDetector(VEHICLE_MODEL)
ocr_reader = LPROCR()
speaker = pyttsx3.init()

cap = cv2.VideoCapture(VIDEO_SOURCE)
if not cap.isOpened():
    print("Cannot open video source:", VIDEO_SOURCE)
    raise SystemExit(1)

print("Entry gate started...")

last_seen = {}
FRAME_DEBOUNCE = 30
frame_idx = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    h, w = frame.shape[:2]


    vehicle_label = "family_sedan"
    try:
        detections_v = vehicle_detector.detect_vehicle(frame)
        if detections_v:
            best = max(detections_v, key=lambda x: x['confidence'])
            vehicle_label = VEHICLE_CLASSES.get(best['class_id'], "family_sedan")
    except:
        pass


    try:
        detections = plate_detector.detect(frame)
    except Exception as e:
        print("Plate detector error:", e)
        detections = []

    for det in detections:
        x1, y1, x2, y2 = det['coords']

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
            print("BAD OCR →", raw_text)
            frame = draw_plate_box(frame, (x1, y1, x2, y2), raw_text)
            continue


        last = last_seen.get(plate_text, -999)
        if frame_idx - last <= FRAME_DEBOUNCE:
            frame = draw_plate_box(frame, (x1, y1, x2, y2), plate_text)
            continue

        last_seen[plate_text] = frame_idx


        try:
            result = handle_entry(plate_text, vehicle_label)
        except Exception as e:
            print("handle_entry error:", e)
            result = {"status": "error", "message": "internal"}

        print("ENTRY:", plate_text, vehicle_label, result)


        if result.get("status") == "ok":
            slot = result.get("slot")
            cv2.putText(frame, f"SLOT: {slot}", (50, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 3)

            try:
                speaker.say(f"Please proceed to slot {slot}")
                speaker.runAndWait()
            except:
                pass

        elif result.get("status") == "exists":
            slot = result.get("slot")
            cv2.putText(frame, f"ALREADY IN: {slot}", (50, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 200, 255), 2)

        frame = draw_plate_box(frame, (x1, y1, x2, y2), plate_text)


    cv2.imshow("Entry Gate", frame)
    if cv2.waitKey(1) == 27:
        break

    frame_idx += 1

cap.release()
cv2.destroyAllWindows()
