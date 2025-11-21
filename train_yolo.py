from ultralytics import YOLO

model = YOLO('yolov8n.pt')

model.train(
    data='/Users/harshlohia/Downloads/parking/data.yaml',
    epochs =50,
    imgsz=416,
    device='mps',
    cache=True
)