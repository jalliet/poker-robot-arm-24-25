import os
import cv2
import json
import time
import queue
import threading
import numpy as np
import pyvirtualcam
from sklearn.cluster import DBSCAN
from ultralytics import YOLO

# =============================================================================
# Global Shared Data and Stop Event
# =============================================================================

# Shared dictionary for the overhead (birds‐eye) frame
shared_frame = {"birds_eye": None}
birds_eye_lock = threading.Lock()

# Thread‐safe event queue for inter-thread communication
event_queue = queue.Queue()

# Global stop event for graceful shutdown
stop_event = threading.Event()

# An event to trigger chip detection on demand
chip_detection_event = threading.Event()


# =============================================================================
# Birds-Eye Camera Thread (Producer)
# =============================================================================
def birds_eye_camera_thread():
    """
    Opens the physical camera (index 0) and, for each frame:
      - Converts the frame from BGR to RGB and sends it to a virtual webcam (via pyvirtualcam)
      - Updates a shared frame (protected by a lock) for fold detection.
    The virtual camera will be available as a “real” device (e.g., device 1)
    that can be passed to the inference pipeline.
    """
    physical_cam_index = 0  # Physical camera index
    cap = cv2.VideoCapture(physical_cam_index)
    if not cap.isOpened():
        event_queue.put({
            "source": "birds_eye_camera",
            "event": "error",
            "message": f"Unable to open physical camera (index {physical_cam_index})."
        })
        return

    # Get camera properties (or set defaults)
    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480
    fps    = cap.get(cv2.CAP_PROP_FPS) or 20

    # Open the virtual camera.
    # The virtual camera will mirror the physical feed.
    try:
        with pyvirtualcam.Camera(width=width, height=height, fps=fps) as virtual_cam:
            print(f"Virtual camera created: {virtual_cam.device}")
            while not stop_event.is_set():
                ret, frame = cap.read()
                if not ret:
                    event_queue.put({
                        "source": "birds_eye_camera",
                        "event": "error",
                        "message": "Failed to capture frame from physical camera."
                    })
                    break

                # Convert frame from BGR to RGB before sending to virtual camera.
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                virtual_cam.send(rgb_frame)
                virtual_cam.sleep_until_next_frame()

                # Also update the shared frame for fold detection.
                with birds_eye_lock:
                    shared_frame["birds_eye"] = frame.copy()

                # (Optional: Display the local feed)
                cv2.imshow("Physical Camera Feed", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    stop_event.set()
                    break

    except Exception as e:
        event_queue.put({
            "source": "birds_eye_camera",
            "event": "error",
            "message": f"Virtual camera error: {e}"
        })
    finally:
        cap.release()
        cv2.destroyWindow("Physical Camera Feed")


# =============================================================================
# Chip Detection Thread (Triggered On-Demand)
# =============================================================================
def chip_detection_thread():
    """
    Opens the chip camera (assumed here at index 1) only when triggered.
    Captures one frame, runs YOLO chip detection, and displays the result.
    """
    model_path = "vision/chips_train/train/weights/best.pt"
    if not os.path.exists(model_path):
        event_queue.put({
            "source": "chip_detection",
            "event": "error",
            "message": f"Chip detection model not found at {model_path}"
        })
        return

    # Load the YOLO chip detection model.
    model = YOLO(model_path)
    chip_values = {'red': 5, 'blue': 10, 'black': 25, 'white': 1}
    class_to_color = {2: 'red', 3: 'white', 1: 'blue', 0: 'black'}

    while not stop_event.is_set():
        if not chip_detection_event.wait(timeout=0.1):
            continue

        # Open chip camera. (Adjust index if needed.)
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
        # cv2.imshow("Chip Detection", annotated_frame)
        # Use a non-blocking wait so the thread doesn't freeze (e.g., 1000 ms delay)
        # cv2.waitKey(1000)
        # cv2.destroyWindow("Chip Detection")
        cap.release()
        chip_detection_event.clear()


# =============================================================================
# Fold Detection Thread (Consumer)
# =============================================================================
def fold_detection_thread():
    """
    Processes the shared birds‐eye frame (updated by the producer thread)
    to detect fold events using DBSCAN clustering. Player area configuration
    is loaded from vision/config.json.
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

    # Extract player areas (keys that include "player")
    PLAYER_AREAS = {name: regions[name] for name in regions if "player" in name}

    # Wait for the first birds‐eye frame to determine dimensions.
    while shared_frame["birds_eye"] is None and not stop_event.is_set():
        time.sleep(0.01)
    with birds_eye_lock:
        frame = shared_frame["birds_eye"].copy()
    frame_height, frame_width = frame.shape[:2]

    def adjust_bounding_box(bbox):
        x, y, w, h = bbox
        x = max(0, min(x, frame_width - 1))
        y = max(0, min(y, frame_height - 1))
        w = max(1, min(w, frame_width - x))
        h = max(1, min(h, frame_height - y))
        return (x, y, w, h)

    PLAYER_AREAS = {name: adjust_bounding_box(bbox) for name, bbox in PLAYER_AREAS.items()}

    def calculate_contour_centers(contours):
        centers = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            centers.append((x + w / 2, y + h / 2))
        return np.array(centers)

    def detect_cards_in_area(frame, player_area, eps=50, min_samples=1):
        x, y, w, h = player_area
        player_region = frame[y:y + h, x:x + w]
        gray = cv2.cvtColor(player_region, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
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
        with birds_eye_lock:
            if shared_frame["birds_eye"] is None:
                continue
            frame = shared_frame["birds_eye"].copy()

        for player_name, player_area in PLAYER_AREAS.items():
            folded, num_centers = detect_cards_in_area(frame, player_area)
            if folded:
                consecutive_fold_counts[player_name] += 1
            else:
                consecutive_fold_counts[player_name] = 0
            is_folded = consecutive_fold_counts[player_name] >= FOLD_THRESHOLD

            x, y, w, h = player_area
            color = (0, 0, 255) if is_folded else (0, 255, 0)
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(frame, f"{player_name}: {num_centers} centers", (x, y - 10),
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
# Hand Tracking Thread (Uses InferencePipeline)
# =============================================================================
def hand_tracking_thread():
    """
    Uses the InferencePipeline to detect hands.
    Since the inference library insists on receiving a device integer,
    we pass the virtual camera’s device index (assumed to be 1) as the video reference.
    """
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

    # Here we assume the virtual camera (created in birds_eye_camera_thread)
    # appears as device index 2.
    virtual_cam_index = 2
    pipeline = InferencePipeline.init(
        model_id="hand_detect-xhlhk/2",  # YOLOv8x model with input size 1280
        video_reference=virtual_cam_index,
        on_prediction=combined_sink,
        api_key="cNMxZM6Ckyg2LD0DiV5n",
    )
    pipeline.start()
    pipeline.join()


# =============================================================================
# Key Listener Thread
# =============================================================================
def key_listener_thread():
    """
    Listens for console input:
      - 'c' triggers chip detection.
      - 'q' or 'esc' stops the application.
    """
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
    """
    Aggregates and (optionally) prints events from various threads.
    """
    while not stop_event.is_set():
        try:
            event = event_queue.get(timeout=0.5)
            # Uncomment the line below to see events printed:
            # print("Event:", event)
        except queue.Empty:
            continue


# =============================================================================
# Main Function: Start All Threads
# =============================================================================
def main():
    threads = []

    # 1. Birds-Eye Camera Thread (Producer):
    birds_eye_thread = threading.Thread(target=birds_eye_camera_thread, name="BirdsEyeCamera", daemon=True)
    threads.append(birds_eye_thread)

    # 2. Chip Detection Thread (Triggered on Demand):
    chip_thread = threading.Thread(target=chip_detection_thread, name="ChipDetection", daemon=True)
    threads.append(chip_thread)

    # 3. Fold Detection Thread (Consumer):
    fold_thread = threading.Thread(target=fold_detection_thread, name="FoldDetection", daemon=True)
    threads.append(fold_thread)

    # 4. Hand Tracking Thread (Uses the virtual cam device index):
    hand_thread = threading.Thread(target=hand_tracking_thread, name="HandTracking", daemon=True)
    threads.append(hand_thread)

    # 5. Event Aggregator Thread:
    aggregator_thread = threading.Thread(target=event_aggregator_thread, name="Aggregator", daemon=True)
    threads.append(aggregator_thread)

    # 6. Key Listener Thread:
    key_thread = threading.Thread(target=key_listener_thread, name="KeyListener", daemon=True)
    threads.append(key_thread)

    # Start all threads.
    for t in threads:
        t.start()
    print("All threads started. Press Ctrl+C or 'q' in the console to exit.")

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
