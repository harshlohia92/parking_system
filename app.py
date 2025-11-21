import streamlit as st
import cv2
import numpy as np
import time
import os
import base64

from detector import PlateDetector
from vehicle_detector import VehicleDetector
from ocr_reader import LPROCR
from parking_logic import handle_entry, handle_exit
from normalize_plate import normalize_plate
from utils import draw_plate_box
from vehicle_map import VEHICLE_CLASSES


PLATE_MODEL = "/Users/harshlohia/Automatic_Number_Plate_Detection_Recognition_YOLOv8/ultralytics/yolo/v8/detect/best.pt"
VEHICLE_MODEL = "/Users/harshlohia/runs/detect/train13/weights/best.pt"


PLATE_DEBOUNCE_SECONDS = 30


@st.cache_resource
def load_models():
    plate_detector = PlateDetector(PLATE_MODEL)
    vehicle_detector = VehicleDetector(VEHICLE_MODEL)
    ocr_reader = LPROCR()
    return plate_detector, vehicle_detector, ocr_reader

plate_detector, vehicle_detector, ocr_reader = load_models()


st.set_page_config(page_title="Smart Parking System", layout="wide")
st.title("🚗 Smart Parking System — Number Plate Recognition")
st.write("Use camera or upload image. Entry / Exit flow with invoice download.")

page = st.sidebar.radio("Mode", ["Entry Gate", "Exit Gate"])
st.sidebar.markdown("---")
st.sidebar.info("Capture a photo with your webcam (Use *Take photo*), or upload an image file.")


if "last_plate_time" not in st.session_state:
    st.session_state["last_plate_time"] = {}  # { plate: timestamp }


def capture_from_camera():
    """Use streamlit's camera_input (returns decoded OpenCV image or None)."""
    img_file_buffer = st.camera_input("Take a photo")
    if img_file_buffer is None:
        return None
    # convert to OpenCV image
    file_bytes = np.asarray(bytearray(img_file_buffer.read()), dtype=np.uint8)
    frame = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    return frame

def load_image(uploaded_img):
    file_bytes = np.frombuffer(uploaded_img.read(), np.uint8)
    return cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

def parse_vehicle_detection(detections_v):
    """
    Return a vehicle_label by handling various detector return formats:
      - ultralytics objects (boxes with .cls and .conf)
      - list of dicts with 'class_id' and 'confidence'
      - list/tuple rows [x1,y1,x2,y2,conf,class]
    """
    default = "family_sedan"
    try:
        if not detections_v:
            return default

        
        first = detections_v[0]
        if hasattr(first, "cls"):
            best = max(detections_v, key=lambda x: float(x.conf))
            cls_id = int(best.cls)
            return VEHICLE_CLASSES.get(cls_id, default)

        
        if isinstance(first, dict):
            best = max(detections_v, key=lambda x: x.get("confidence", 0))
            cls_id = best.get("class_id", None)
            if cls_id is not None:
                return VEHICLE_CLASSES.get(int(cls_id), default)
            return default

        
        if isinstance(first, (list, tuple)) and len(first) >= 6:
            best = max(detections_v, key=lambda x: x[4])
            cls_id = int(best[5])
            return VEHICLE_CLASSES.get(cls_id, default)

    except Exception:
        pass
    return default

def show_invoice_download_from_path(path, label="Download Invoice"):
    """Try to read invoice file and expose download button; fallback to create text invoice."""
    if path and os.path.exists(path):
        try:
            with open(path, "rb") as f:
                data = f.read()
            invoice_name = os.path.basename(path)
            st.download_button(label=label, data=data, file_name=invoice_name, mime="text/plain")
            return
        except Exception:
            pass

  

def make_invoice_text(plate, minutes, amount):
    tnow = time.strftime("%Y-%m-%d %H:%M:%S")
    return f"""===== PARKING INVOICE =====
Plate: {plate}
Entry/Exit: {tnow}
Duration (min): {minutes}
Amount: ₹{amount}
===========================
"""

def plate_debounced(plate):
    """Return True if plate is allowed (not debounced), and register timestamp."""
    now = time.time()
    last = st.session_state["last_plate_time"].get(plate, 0)
    if now - last < PLATE_DEBOUNCE_SECONDS:
        return False
    st.session_state["last_plate_time"][plate] = now
    return True


col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Input")
    use_camera = st.checkbox("Use Camera (take photo)", value=False)
    uploaded_img = None
    frame = None

    if use_camera:
        frame = capture_from_camera()
    else:
        uploaded_img = st.file_uploader("Upload image", type=["jpg", "jpeg", "png"])
        if uploaded_img:
            frame = load_image(uploaded_img)

    if frame is not None:
        
        st.image(frame, channels="BGR", caption="Input Image", use_container_width=True)

with col2:
    st.subheader("Result")
    plate_display = st.empty()
    status_display = st.empty()
    invoice_area = st.empty()


if 'frame' in locals() and frame is not None:

    
    try:
        detections = plate_detector.detect(frame)
    except Exception as e:
        st.error(f"Plate detector error: {e}")
        detections = []

    if not detections:
        status_display.error("No number plate detected.")
    else:
        
        det = detections[0]
        x1, y1, x2, y2 = det["coords"]
        
        h, w = frame.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        crop = frame[y1:y2, x1:x2]

       
        preview = frame.copy()
        preview = draw_plate_box(preview, (x1, y1, x2, y2), "")
        st.image(preview, channels="BGR", caption="Detected Plate Region (boxed)")

       
        try:
            raw_text = ocr_reader.read_text(crop)
        except Exception as e:
            raw_text = None
            st.warning(f"OCR error: {e}")

        plate_display.write(f"**Raw OCR:** `{raw_text}`")

        if not raw_text:
            status_display.error("OCR failed or returned no text.")
        else:
            plate_text = normalize_plate(raw_text)
            if not plate_text:
                status_display.error("Could not normalize plate from OCR result.")
            else:
                plate_display.success(f"Detected Plate: **{plate_text}**")

               
                if not plate_debounced(plate_text):
                    status_display.info(f"Plate {plate_text} recently processed — wait {PLATE_DEBOUNCE_SECONDS}s")
                else:
                   
                    if page == "Entry Gate":
                        
                        vehicle_label = "family_sedan"
                        try:
                            detections_v = vehicle_detector.detect_vehicle(frame)
                        except Exception:
                            detections_v = None
                        vehicle_label = parse_vehicle_detection(detections_v)

                        
                        try:
                            res = handle_entry(plate_text, vehicle_label)
                        except Exception as e:
                            res = {"status": "error", "message": str(e)}

                        if res.get("status") == "ok":
                            slot = res.get("slot", "N/A")
                            status_display.info(
                                f"✅ Entry Recorded\n\nPlate: **{plate_text}**\n\nSlot Assigned: **{slot}**\n\nVehicle Type: **{vehicle_label}**"
                            )
                        elif res.get("status") == "exists":
                            status_display.warning(f"Vehicle already inside. Slot: {res.get('slot')}")
                        elif res.get("status") == "full":
                            status_display.error("Parking Full.")
                        else:
                            status_display.error(f"Entry failed: {res.get('message')}")

                        invoice_area.empty()

                    
                    else:
                        try:
                            res = handle_exit(plate_text)
                        except Exception as e:
                            res = {"status": "error", "message": str(e)}

                        if res.get("status") == "ok":
                            minutes = res.get("minutes", res.get("duration", "N/A"))
                            amount = res.get("amount", 0)
                            slot_rel = res.get("slot_released", None)

                            status_display.success(
                                f"✅ Exit Completed\n\nPlate: **{plate_text}**\n\nSlot Freed: **{slot_rel}**\n\nDuration: **{minutes}** mins\n\nAmount: **₹{amount}**"
                            )

                           
                            invoice_path = res.get("invoice")
                            if invoice_path and os.path.exists(invoice_path):
                                
                                with invoice_area:
                                    show_invoice_download_from_path(invoice_path, label="📄 Download Invoice (file)")
                            else:
                                
                                invoice_txt = make_invoice_text(plate_text, minutes, amount)
                                with invoice_area:
                                    st.download_button(
                                        label="📄 Download Invoice (generated)",
                                        data=invoice_txt,
                                        file_name=f"invoice_{plate_text}.txt",
                                        mime="text/plain"
                                    )
                        else:
                            status_display.error(f"Exit failed: {res.get('message')}")


st.markdown("---")
st.markdown("Developed for Smart Parking — capture or upload an image to register entry/exit.")
