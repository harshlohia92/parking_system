from ultralytics import YOLO

class VehicleDetector:
    def __init__(self, model_path):
        self.model = YOLO(model_path)

    def detect_vehicle(self, frame, conf=0.35):
        """
        Returns list of {'class_id': int, 'confidence': float, 'coords': (x1,y1,x2,y2)}
        """
        result = self.model(frame, conf=conf, verbose=False)
        detections = []
        for r in result:
            for box in r.boxes:
                cls = int(box.cls[0].cpu().numpy()) if hasattr(box.cls[0], 'cpu') else int(box.cls[0])
                conf_score = float(box.conf[0].cpu().numpy()) if hasattr(box.conf[0], 'cpu') else float(box.conf[0])
                xyxy = box.xyxy[0].cpu().numpy() if hasattr(box.xyxy[0], 'cpu') else box.xyxy[0]
                x1, y1, x2, y2 = map(int, xyxy)
                detections.append({"class_id": cls, "confidence": conf_score, "coords": (x1, y1, x2, y2)})
        return detections
