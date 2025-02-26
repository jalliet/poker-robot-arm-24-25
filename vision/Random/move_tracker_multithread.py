import cv2
import threading
import queue
import json
import time
import numpy as np
from sklearn.cluster import DBSCAN
from inference import InferencePipeline
from inference.core.interfaces.stream.sinks import render_boxes
from inference.core.interfaces.camera.entities import VideoFrame
import torch
from ultralytics import YOLO
import os
from dotenv import load_dotenv

# Load the environment variables
load_dotenv()

CONFIG_FILE = "vision/config.json"

# Load player areas from config
def load_config():
    """Loads saved player, pot, and community card locations."""
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)
regions = load_config()

PLAYER_AREAS = {name: regions[name] for name in regions if "player" in name}
POT_AREA = regions.get("pot_area", (0, 0, 100, 100))
COMMUNITY_CARDS = regions.get("community_cards", (0, 0, 200, 100))
ALL_AREAS = {**PLAYER_AREAS, "pot": POT_AREA, "community_cards": COMMUNITY_CARDS}

# Thread-safe queues for sending updates to main thread
hand_queue = queue.Queue()
fold_queue = queue.Queue()
chip_queue = queue.Queue()

# Camera setup
camera_1 = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Bird's eye view
camera_2 = cv2.VideoCapture(1, cv2.CAP_DSHOW)  # Close-up for chip counting

# Ensure cameras opened successfully
if not camera_1.isOpened() or not camera_2.isOpened():
    print("Error: Could not open cameras.")
    exit()
    
chip_capture_requested = threading.Event()

# ==============================
#  HAND DETECTION THREAD (YOLOv8)
# ==============================
def detect_hands():
    def calculate_overlap(hand_bbox, area_bbox):
        """Calculates the overlap area between a detected hand and a defined region."""
        hx, hy, hw, hh = hand_bbox
        ax, ay, aw, ah = area_bbox

        # Calculate the intersection rectangle
        x_overlap = max(0, min(hx + hw, ax + aw) - max(hx, ax))
        y_overlap = max(0, min(hy + hh, ay + ah) - max(hy, ay))

        return x_overlap * y_overlap  # Return area of overlap

    def my_custom_sink(predictions: dict, video_frame: VideoFrame):
        hands_detected = {area: [] for area in ALL_AREAS}  # Allow multiple hands per area

        for p in predictions['predictions']:
            center_x, center_y = p['x'], p['y']
            width, height = p['width'], p['height']
            hand_bbox = (center_x - width // 2, center_y - height // 2, width, height)

            # Find the area with the **most** overlap
            max_overlap = 0
            best_area = None

            for area_name, area_bbox in ALL_AREAS.items():
                overlap = calculate_overlap(hand_bbox, area_bbox)
                if overlap > max_overlap:
                    max_overlap = overlap
                    best_area = area_name

            if best_area:
                hands_detected[best_area].append((center_x, center_y))  # Store multiple hands per area

        # Remove empty areas (for cleaner output)
        hands_detected = {k: v for k, v in hands_detected.items() if v}

        # Send detected hands to main thread **only if changed**
        if hands_detected:
            hand_queue.put(hands_detected)
    
    # New function to call both render_boxes and my_custom_sink
    def combined_sink(predictions: dict, video_frame: VideoFrame):
        render_boxes(predictions, video_frame)
        my_custom_sink(predictions, video_frame)

    # Start YOLO-based inference pipeline
    pipeline = InferencePipeline.init(
        model_id="hand_detect-xhlhk/2",
        video_reference=0,
        on_prediction=combined_sink,
        api_key=os.getenv("API_REFERENCE_KEY")
    )
    pipeline.start()
    pipeline.join()

# ==============================
#  FOLD DETECTION THREAD
# ==============================
def detect_folds():
    last_folds = set()

    def calculate_contour_centers(contours):
        centers = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            center = (x + w / 2, y + h / 2)
            centers.append(center)
        return np.array(centers)

    while True:
        ret, frame = camera_1.read()
        if not ret:
            print("Fold Detection: Camera feed error")
            break

        new_folds = set()  # Store folded players
        for player, (x, y, w, h) in PLAYER_AREAS.items():
            player_region = frame[y:y+h, x:x+w]
            gray = cv2.cvtColor(player_region, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Canny(blurred, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            centers = calculate_contour_centers(contours)
            
            if len(centers) > 0:
                clustering = DBSCAN(eps=50, min_samples=1).fit(centers)
                if len(set(clustering.labels_)) > 0:
                    new_folds.add(player)

            # Display edges detection
            #cv2.imshow(f"Edges Detection - {player}", edges)

        # Send update **only if** fold status changed
        if new_folds != last_folds:
            fold_queue.put(new_folds)
            last_folds = new_folds.copy()

        cv2.waitKey(1)  # Add a small delay to allow window updates

# ==============================
#  CHIP COUNTING THREAD
# ==============================
def count_chips():
    last_chip_count = None
    
    # Hardcoded values for different chip colors
    chip_values = {
        'red': 5,
        'blue': 10,
        'black': 25,
        'white': 1
    }

    # Class-to-color mapping
    class_to_color = {
        2: 'red',
        3: 'white',
        1: 'blue',
        0: 'black'
    }
    
    # Load the YOLO model
    model_path = "vision/chips_train/train/weights/best.pt"
    if not os.path.exists(model_path):
        print(f"Error: Model weights not found at {model_path}")
        return
    model = YOLO(model_path) 
    
    while True:
        ret, frame = camera_2.read()
        if not ret:
            print("Chip Counting: Camera feed error")
            break

        cv2.imshow("Camera 2 Feed", frame)
        cv2.waitKey(1)

        if chip_capture_requested.is_set():
            print("Key 'c' pressed. Capturing photo and counting chips...")
            x, y, w, h = POT_AREA
            pot_region = frame[y:y+h, x:x+w]

            results = model(pot_region, show=False)

            total_value = 0
            for result in results:
                for box in result.boxes:
                    chip_class = int(box.cls.item())
                    chip_color = class_to_color.get(chip_class, None)
                    if chip_color and chip_color in chip_values:
                        total_value += chip_values[chip_color]

            print(f"Total value of the pot: ${total_value}")

            annotated_frame = results[0].plot()
            cv2.imshow("YOLO Detection", annotated_frame)
            cv2.waitKey(1)

            # Send chip count to main thread
            chip_queue.put(total_value)

            # Reset the event after processing
            chip_capture_requested.clear()

# ==============================
#  MAIN THREAD - PROCESS DATA
# ==============================
def main_loop():
    while True:
        key = cv2.waitKey(1) & 0xFF
        if key in (ord('c'), ord('C')):
            print("Chip count request sent...")
            chip_capture_requested.set()
        elif key in (ord('q'), ord('Q')):
            print("Exiting main loop...")
            break

        # Initialize variables before the try-except blocks
        hands = None
        folds = None
        chip_count = None

        # Get latest data from queues if available
        try:
            hands = hand_queue.get_nowait()
        except queue.Empty:
            pass
        
        try:
            folds = fold_queue.get_nowait()
        except queue.Empty:
            pass

        try:
            chip_count = chip_queue.get_nowait()
        except queue.Empty:
            pass

        # **Process Hands**
        if hands is not None:
            print(f"\n[HAND DETECTION] {hands}")

        # **Process Folds**
        if folds is not None:
            for player in folds:
                print(f"[FOLD DETECTION] {player} has folded!")

        # **Process Chip Count**
        if chip_count is not None:
            print(f"[CHIP COUNT] New pot value: {chip_count}")

        # Display a blank window to ensure cv2.waitKey is called
        cv2.imshow("Main Loop", np.zeros((100, 100, 3), dtype=np.uint8))
        cv2.waitKey(1)

# ==============================
#  START THREADS
# ==============================
hand_thread = threading.Thread(target=detect_hands, daemon=True)
fold_thread = threading.Thread(target=detect_folds, daemon=True)
chip_thread = threading.Thread(target=count_chips, daemon=True)  

hand_thread.start()
fold_thread.start()
chip_thread.start()

# Run main loop
main_loop()

