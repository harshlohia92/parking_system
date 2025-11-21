import cv2

def draw_plate_box(frame, coords, plate_text):
    x1, y1, x2, y2 = coords
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
    if plate_text:
        cv2.putText(frame, plate_text, (x1, max(0, y1 - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    return frame

def preprocess_plate(crop):

    try:
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    except Exception:
        return crop
    gray = cv2.resize(gray, (400, 100))
    gray = cv2.bilateralFilter(gray, 11, 17, 17)
    thresh = cv2.adaptiveThreshold(gray, 255,
                                   cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY, 11, 2)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    clean = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    return clean
