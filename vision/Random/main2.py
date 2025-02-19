import os
import cv2
import json
import time
import queue
import threading
import numpy as np
from sklearn.cluster import DBSCAN
from ultralytics import YOLO

# =============================================================================
# Global Queues and Stop Event
# =============================================================================
fold_queue = queue.Queue(maxsize=10)
hand_queue = queue.Queue(maxsize=10)
event_queue = queue.Queue()
stop_event = threading.Event()
chip_detection_event = threading.Event()

# =============================================================================
# Birds-Eye Camera Producer Thread
# =============================================================================

def birds_eye_camera_thread():
    """
    Opens the birds‐eye camera and pushes each captured frame into both
    fold_queue and hand_queue.
    """
    cam_index = 0  # adjust as needed
    while not stop_event.is_set():
        cap = cv2.VideoCapture(cam_index)
        if not cap.isOpened():
            event_queue.put({
                "source": "birds_eye_camera",
                "event": "error",
                "message": f"Unable to open birds‐eye camera (index {cam_index})."
            })
            time.sleep(0.5)
            continue

        while not stop_event.is_set():
            ret, frame = cap.read()
            if not ret:
                event_queue.put({
                    "source": "birds_eye_camera",
                    "event": "error",
                    "message": "Failed to capture frame from birds‐eye camera."
                })
                break  # reinitialize camera

            try:
                fold_queue.put_nowait(frame.copy())
            except queue.Full:
                pass
            try:
                hand_queue.put_nowait(frame.copy())
            except queue.Full:
                pass

            time.sleep(0.01)
        cap.release()
        time.sleep(0.5)

# =============================================================================
# Fold Detection Consumer Thread
# =============================================================================

def fold_detection_thread():
    """
    Processes frames from fold_queue for fold detection.
    """
    CONFIG_FILE = "vision/config.json"
    try:
        with open(CONFIG_FILE, "r") as f:
            regions = json.load(f)
    except Exception as e:
        event_queue.put({
            "source": "fold_detection",
            "event": "error",
            "message": f"Failed to load config: {e}"
        })
        return

    # Get player areas from the config
    PLAYER_AREAS = {name: regions[name] for name in regions if "player" in name}
    frame_width = frame_height = None

    def adjust_bounding_box(bbox, fw, fh):
        x, y, w, h = bbox
        x = max(0, min(x, fw - 1))
        y = max(0, min(y, fh - 1))
        w = max(1, min(w, fw - x))
        h = max(1, min(h, fh - y))
        return (x, y, w, h)

    # Wait for first frame to know dimensions
    while not stop_event.is_set():
        try:
            frame = fold_queue.get(timeout=0.1)
            frame_height, frame_width = frame.shape[:2]
            break
        except queue.Empty:
            continue

    PLAYER_AREAS = {name: adjust_bounding_box(bbox, frame_width, frame_height)
                    for name, bbox in PLAYER_AREAS.items()}

    def calculate_contour_centers(contours):
        centers = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            centers.append((x + w/2, y + h/2))
        return np.array(centers)

    def detect_cards_in_area(frame, player_area, eps=50, min_samples=1):
        x, y, w, h = player_area
        region = frame[y:y+h, x:x+w]
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5,5), 0)
        edges = cv2.Canny(blurred, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        centers = calculate_contour_centers(contours)
        if len(centers) > 0:
            clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(centers)
            labels = clustering.labels_
            num_centers = len(set(labels)) if labels is not None else 0
            return True, num_centers
        return False, 0

    consecutive_fold_counts = {player: 0 for player in PLAYER_AREAS.keys()}
    FOLD_THRESHOLD = 30

    while not stop_event.is_set():
        try:
            frame = fold_queue.get(timeout=0.05)
        except queue.Empty:
            continue

        for player_name, player_area in PLAYER_AREAS.items():
            folded, num_centers = detect_cards_in_area(frame, player_area)
            if folded:
                consecutive_fold_counts[player_name] += 1
            else:
                consecutive_fold_counts[player_name] = 0
            is_folded = consecutive_fold_counts[player_name] >= FOLD_THRESHOLD

            x, y, w, h = player_area
            color = (0, 0, 255) if is_folded else (0, 255, 0)
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            cv2.putText(frame, f"{player_name}: {num_centers} centers", (x, y-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            if is_folded:
                event_queue.put({
                    "source": "fold_detection",
                    "event": "fold_detected",
                    "player": player_name,
                    "num_centers": num_centers
                })

        cv2.imshow("Fold Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            stop_event.set()
            break
        time.sleep(0.01)
    cv2.destroyWindow("Fold Detection")

# =============================================================================
# Custom VideoCapture-like Class for Hand Tracking
# =============================================================================

class QueueVideoCapture:
    """
    A simple object that mimics the VideoCapture interface using frames from a queue.
    """
    def __init__(self, frame_queue):
        self.frame_queue = frame_queue
        self.stopped = False
        self.width = 640   # default width
        self.height = 480  # default height

    def isOpened(self):
        # Return True if not explicitly stopped.
        return not self.stopped

    def start(self):
        # Optionally, grab one frame to set properties if available.
        ret, frame = self.read()
        if ret and frame is not None:
            self.height, self.width = frame.shape[:2]
        return self

    def read(self):
        try:
            frame = self.frame_queue.get(timeout=0.05)
            # Update dimensions based on the frame if available.
            if frame is not None:
                self.height, self.width = frame.shape[:2]
            return True, frame
        except queue.Empty:
            return False, None

    def get(self, propId):
        # Support common properties.
        if propId == cv2.CAP_PROP_FRAME_WIDTH:
            return self.width
        elif propId == cv2.CAP_PROP_FRAME_HEIGHT:
            return self.height
        else:
            # Return 0 for properties we don't support.
            return 0

    def release(self):
        self.stopped = True



# =============================================================================
# Hand Tracking Consumer Thread with Monkey-Patching
# =============================================================================

def hand_tracking_thread():
    """
    Uses the InferencePipeline to detect hands. We pass a custom video source
    based on our QueueVideoCapture. To prevent the pipeline from calling
    cv2.VideoCapture on our object, we monkey-patch cv2.VideoCapture.
    """
    # Import the inference pipeline modules
    from inference import InferencePipeline
    from inference.core.interfaces.stream.sinks import render_boxes
    from inference.core.interfaces.camera.entities import VideoFrame

    def my_custom_sink(predictions: dict, video_frame: VideoFrame):
        for p in predictions.get('predictions', []):
            event_queue.put({
                "source": "hand_tracking",
                "event": "hand_detected",
                "x": p['x'],
                "y": p['y']
            })

    def combined_sink(predictions: dict, video_frame: VideoFrame):
        render_boxes(predictions, video_frame)
        my_custom_sink(predictions, video_frame)

    # Create our custom video source from hand_queue.
    custom_source = QueueVideoCapture(hand_queue)

    # Monkey-patch cv2.VideoCapture so that if our custom_source is passed,
    # it returns the object itself.
    original_VideoCapture = cv2.VideoCapture

    def patched_VideoCapture(source, *args, **kwargs):
        if isinstance(source, QueueVideoCapture):
            return source
        return original_VideoCapture(source, *args, **kwargs)

    cv2.VideoCapture = patched_VideoCapture

    # Create the inference pipeline with our custom source.
    pipeline = InferencePipeline.init(
        model_id="hand_detect-xhlhk/2",  # yolov8x model with input size 1280
        video_reference=custom_source,   # pass our custom video source
        on_prediction=combined_sink,
        api_key="cNMxZM6Ckyg2LD0DiV5n",
    )

    pipeline.start()
    pipeline.join()

    # (Optionally, restore the original VideoCapture if needed)
    cv2.VideoCapture = original_VideoCapture

# =============================================================================
# Chip Detection Thread (Unchanged)
# =============================================================================

def chip_detection_thread():
    """
    Performs chip detection when triggered.
    """
    model_path = "vision/chips_train/train/weights/best.pt"

    if not os.path.exists(model_path):
        event_queue.put({
            "source": "chip_detection",
            "event": "error",
            "message": f"Chip detection model not found at {model_path}"
        })
        return

    model = YOLO(model_path)
    chip_values = {'red': 5, 'blue': 10, 'black': 25, 'white': 1}
    class_to_color = {2: 'red', 3: 'white', 1: 'blue', 0: 'black'}

    while not stop_event.is_set():
        if not chip_detection_event.wait(timeout=0.1):
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
        cv2.imshow("Chip Detection", annotated_frame)
        cv2.waitKey(0)
        cv2.destroyWindow("Chip Detection")
        cap.release()
        chip_detection_event.clear()

# =============================================================================
# Key Listener Thread
# =============================================================================

def key_listener_thread():
    while not stop_event.is_set():
        user_input = input("Press 'c' to count chips (or 'q' to quit): ").strip().lower()
        if user_input == 'c':
            chip_detection_event.set()
        elif user_input in ['q', 'esc']:
            stop_event.set()
            break
        time.sleep(0.1)

# =============================================================================
# Event Aggregator Thread
# =============================================================================

def event_aggregator_thread():
    while not stop_event.is_set():
        try:
            event = event_queue.get(timeout=0.5)
            print("Event:", event)
        except queue.Empty:
            continue

# =============================================================================
# Main Function: Start All Threads
# =============================================================================

def main():
    threads = []

    producer_thread = threading.Thread(target=birds_eye_camera_thread,
                                       name="BirdsEyeCameraProducer", daemon=True)
    threads.append(producer_thread)

    fold_thread = threading.Thread(target=fold_detection_thread,
                                   name="FoldDetectionConsumer", daemon=True)
    threads.append(fold_thread)

    hand_thread = threading.Thread(target=hand_tracking_thread,
                                   name="HandTrackingConsumer", daemon=True)
    threads.append(hand_thread)

    chip_thread = threading.Thread(target=chip_detection_thread,
                                   name="ChipDetection", daemon=True)
    threads.append(chip_thread)

    aggregator_thread = threading.Thread(target=event_aggregator_thread,
                                         name="Aggregator", daemon=True)
    threads.append(aggregator_thread)

    key_thread = threading.Thread(target=key_listener_thread,
                                  name="KeyListener", daemon=True)
    threads.append(key_thread)

    for t in threads:
        t.start()

    print("All threads started. Press Ctrl+C or 'q' to exit.")
    try:
        while not stop_event.is_set():
            time.sleep(0.1)
    except KeyboardInterrupt:
        stop_event.set()
        print("KeyboardInterrupt detected, exiting.")

    for t in threads:
        t.join()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

