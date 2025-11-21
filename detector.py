from ultralytics import YOLO

class PlateDetector:
    def __init__(self, model_path):
        self.model = YOLO(model_path)

    def detect(self, frame, conf=0.35):
        """
        Returns list of detections: {'coords':(x1,y1,x2,y2),'confidence':float}
        """
        result = self.model(frame, conf=conf, verbose=False)
        detection = []
        for r in result:
            for box in r.boxes:
                xyxy = box.xyxy[0].cpu().numpy() if hasattr(box.xyxy[0], 'cpu') else box.xyxy[0]
                x1, y1, x2, y2 = map(int, xyxy)
                conf_score = float(box.conf[0].cpu().numpy()) if hasattr(box.conf[0], 'cpu') else float(box.conf[0])
                detection.append({'coords': (x1, y1, x2, y2), "confidence": conf_score})
        return detection

    def crop(self, frame, coords):
        x1, y1, x2, y2 = coords
        h, w = frame.shape[:2]
        x1 = max(0, x1); y1 = max(0, y1); x2 = min(w, x2); y2 = min(h, y2)
        return frame[y1:y2, x1:x2]
