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
    "box": "paper",
}


class VisionNode:
    def __init__(self, model_path=None, image_path=None, confidence_threshold=0.45):
        self.image_path = image_path or IMAGE_PATH
        self.confidence_threshold = confidence_threshold
        os.makedirs(os.path.dirname(self.image_path) or ".", exist_ok=True)

        print("[VISION] Loading YOLO model...")
        self.model = YOLO(model_path or YOLO_MODEL)
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

                if confidence < self.confidence_threshold:
                    continue
                if label not in CLASS_MAP:
                    continue

                if best_detection is None or confidence > best_detection["confidence"]:
                    best_detection = {
                        "yolo_label": label,
                        "broad_class": CLASS_MAP[label],
                        "confidence": confidence,
                        "image_path": self.image_path,
                    }

        if best_detection:
            cv2.imwrite(self.image_path, frame)

        return best_detection

    def detect_person(self, frame, confidence_threshold=0.5):
        results = self.model(frame, verbose=False)
        best_person = None

        for result in results:
            if result.boxes is None:
                continue

            for box in result.boxes:
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                label = self.model.names[class_id]

                if label != "person" or confidence < confidence_threshold:
                    continue

                if best_person is None or confidence > best_person["confidence"]:
                    best_person = {
                        "yolo_label": label,
                        "confidence": confidence,
                    }

        return best_person
