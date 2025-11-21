import os
from PIL import Image


dataset_root = "/Users/harshlohia/Downloads/parking/vehicle"
train_folder = os.path.join(dataset_root, "train")
val_folder   = os.path.join(dataset_root, "val")


classes = [
    "bus", "family sedan", "suv", "jeep", "minibus",
    "heavy truck", "fire engine", "taxi", "truck", "racing car"
]


def create_yolo_labels(folder_path):
    for class_id, class_name in enumerate(classes):
        class_folder = os.path.join(folder_path, class_name)
        if not os.path.exists(class_folder):
            print(f"Folder not found: {class_folder}")
            continue

        for img_name in os.listdir(class_folder):
            if not img_name.lower().endswith((".jpg", ".png")):
                continue

            img_path = os.path.join(class_folder, img_name)
            try:
                img = Image.open(img_path)
                w, h = img.size
            except Exception as e:
                print(f"Cannot open {img_path}: {e}")
                continue


            x_center, y_center = 0.5, 0.5
            width, height = 1.0, 1.0

            label_path = os.path.join(class_folder, img_name.rsplit(".", 1)[0] + ".txt")
            with open(label_path, "w") as f:
                f.write(f"{class_id} {x_center} {y_center} {width} {height}\n")

            print(f"Labeled: {img_path}")

print("Creating YOLO labels for TRAIN folder...")
create_yolo_labels(train_folder)

print("Creating YOLO labels for VAL folder...")
create_yolo_labels(val_folder)

print("YOLO labels generated successfully!")
