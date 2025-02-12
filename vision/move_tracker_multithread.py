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

CONFIG_FILE = "config.json"

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
camera_2 = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Close-up for chip counting

# Ensure cameras opened successfully
if not camera_1.isOpened() or not camera_2.isOpened():
    print("Error: Could not open cameras.")
    exit()

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
        api_key="cNMxZM6Ckyg2LD0DiV5n"
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

        # Send update **only if** fold status changed
        if new_folds != last_folds:
            fold_queue.put(new_folds)
            last_folds = new_folds.copy()


# ==============================
#  CHIP COUNTING THREAD
# ==============================
def count_chips():
    last_chip_count = None

    while True:
        ret, frame = camera_2.read()
        if not ret:
            print("Chip Counting: Camera feed error")
            break

        x, y, w, h = POT_AREA
        pot_region = frame[y:y+h, x:x+w]
        
        # Simulated chip counting (Replace with real model inference)
        chip_count = np.random.randint(0, 100)  # Simulated chip count
        
        # Send update **only if** chip count changes
        if chip_count != last_chip_count:
            chip_queue.put(chip_count)
            last_chip_count = chip_count


# ==============================
#  MAIN THREAD - PROCESS DATA
# ==============================
def main_loop():
    while True:
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

