import os
import cv2
from ultralytics import YOLO


YOLO_MODEL = "yolo11n.pt"
IMAGE_PATH = "captures/latest_waste.jpg"


CLASS_MAP = {
    "bottle": "plastic",
    "cup": "plastic",
    "wine glass": "glass",
    "book": "paper",
    "cell phone": "e-waste",
    "fork": "metal",
    "knife": "metal",
    "spoon": "metal",
    "scissors": "metal",
    "cardboard box": "paper",
    "box" : "paper"
}


class VisionNode:
    def __init__(self):
        os.makedirs("captures", exist_ok=True)

        print("[VISION] Loading YOLO model...")
        self.model = YOLO(YOLO_MODEL)
        print("[VISION] YOLO loaded.")

    def detect_waste(self, frame):
        results = self.model(frame, verbose=False)

        best_detection = None

        for result in results:
            if result.boxes is None:
                continue

            for box in result.boxes:
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                label = self.model.names[class_id]

                if confidence < 0.45:
                    continue

                if label not in CLASS_MAP:
                    continue

                if best_detection is None or confidence > best_detection["confidence"]:
                    best_detection = {
                        "yolo_label": label,
                        "broad_class": CLASS_MAP[label],
                        "confidence": confidence,
                        "image_path": IMAGE_PATH,
                    }

        if best_detection:
            cv2.imwrite(IMAGE_PATH, frame)

        return best_detection