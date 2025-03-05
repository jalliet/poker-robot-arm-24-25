import os
import cv2
import json
from ultralytics import YOLO
import threading
import queue

def chip_detection_thread(event_queue, stop_event, chip_detection_event):
    model_path = "vision/chips_train/train/weights/best.pt"
    if not os.path.exists(model_path):
        event_queue.put({
            "source": "chip_detection",
            "event": "error",
            "message": f"Chip detection model not found at {model_path}"
        })
        return

    model = YOLO(model_path)
    
    with open("vision/config.json", "r") as f:
        config = json.load(f)
    
    chip_values = config["chip_values"] 

    class_to_color = {2: 'red', 3: 'white', 1: 'blue', 0: 'black'}

    while not stop_event.is_set():
        if not chip_detection_event.wait(0.1):
            continue

        cap = cv2.VideoCapture(1)
        if not cap.isOpened():
            event_queue.put({
                "source": "chip_detection",
                "event": "error",
                "message": "Unable to open chip camera (index 1)."
            })
            chip_detection_event.clear()
            continue

        ret, frame = cap.read()
        if not ret:
            event_queue.put({
                "source": "chip_detection",
                "event": "error",
                "message": "Failed to capture frame from chip camera."
            })
            cap.release()
            chip_detection_event.clear()
            continue

        event_queue.put({
            "source": "chip_detection",
            "event": "info",
            "message": "Capturing photo and counting chips..."
        })

        results = model(frame, show=False)
        total_value = 0
        for result in results:
            for box in result.boxes:
                chip_class = int(box.cls.item())
                chip_color = class_to_color.get(chip_class)
                if chip_color in chip_values:
                    total_value += chip_values[chip_color]

        event_queue.put({
            "source": "chip_detection",
            "event": "chip_count",
            "total_value": total_value
        })

        annotated_frame = results[0].plot() if results else frame
        cap.release()
        chip_detection_event.clear()