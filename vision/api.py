from flask import Flask, request, jsonify
import threading
import cv2
import numpy as np
import torch
from ultralytics import YOLO  # YOLOv8
import time
from sklearn.cluster import DBSCAN

app = Flask(__name__)

move_tracker = None  # Will hold an instance of MoveTracker

# Initialize the YOLO models
chip_model = YOLO("train/train/weights/best.pt")  
card_model = YOLO("train/train/weights/best.pt")  

class MoveTracker(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        # Initialize webcam
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Error: Could not open camera.")
            raise Exception("Could not open camera.")

        ret, frame = self.cap.read()
        if not ret:
            print("Error: Failed to capture initial frame.")
            self.cap.release()
            raise Exception("Failed to capture initial frame.")

        self.frame_height, self.frame_width = frame.shape[:2]
        print(f"Frame dimensions: Width={self.frame_width}, Height={self.frame_height}")

        # Define player areas and pot area
        self.PLAYER_AREAS = {
            "player_1": (0, 325, 150, 150),
            "player_2": (175, 325, 150, 150),
            "player_3": (350, 325, 150, 150),
            "player_4": (525, 325, 150, 150)
        }

        self.POT_AREA = (0, 100, 200, 200)
        # Adjust bounding boxes
        self.adjust_bounding_boxes()

        # Initialize motion tracking info
        self.init_motion_info()

        self.active_players = ["player_1", "player_2", "player_3", "player_4"]
        self.current_player_index = 0
        self.move_history = {player: None for player in self.active_players}

        self.cooldown_time = 3.0
        self.bet_opened = False  # Indicates if a call/raise has occurred
        self.last_action_time = time.time()

        self.running = False  # Flag to control the thread
        self.lock = threading.Lock()

    def adjust_bounding_box(self, area_name, bbox):
        x, y, w, h = bbox
        x = max(0, min(x, self.frame_width - 1))
        y = max(0, min(y, self.frame_height - 1))
        w = max(1, min(w, self.frame_width - x))
        h = max(1, min(h, self.frame_height - y))
        return (x, y, w, h)

    def adjust_bounding_boxes(self):
        self.POT_AREA = self.adjust_bounding_box("pot", self.POT_AREA)
        self.PLAYER_AREAS = {name: self.adjust_bounding_box(name, bbox) for name, bbox in self.PLAYER_AREAS.items()}

    def init_motion_info(self):
        # Initialize motion tracking information for each area
        self.AREAS = {"pot": self.POT_AREA}
        self.AREAS.update(self.PLAYER_AREAS)

        self.motion_info = {}
        for area in self.AREAS.keys():
            self.motion_info[area] = {
                "fgbg": cv2.createBackgroundSubtractorMOG2(),
                "last_mean": 0.0,
                "motion_detected_time": 0.0
            }

    def detect_movement(self, frame, area_name):
        x, y, w, h = self.AREAS[area_name]
        roi = frame[y:y + h, x:x + w]
        fgbg = self.motion_info[area_name]["fgbg"]
        fgmask = fgbg.apply(roi)

        current_mean = np.mean(fgmask)
        result = abs(current_mean - self.motion_info[area_name]["last_mean"])
        self.motion_info[area_name]["last_mean"] = current_mean

        threshold = 0.3  # Adjust as needed
        if result > threshold and (time.time() - self.motion_info[area_name]["motion_detected_time"]) > self.cooldown_time:
            self.motion_info[area_name]["motion_detected_time"] = time.time()
            return True
        else:
            return False

    def calculate_contour_centers(self, contours):
        centers = []
        for cnt in contours:
            M = cv2.moments(cnt)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                centers.append([cX, cY])
        return np.array(centers)

    def detect_cards_in_area(self, frame, player_area, eps=50, min_samples=1, debug=False):
        x, y, w, h = player_area
        player_region = frame[y:y + h, x:x + w]

        # Convert to grayscale and apply edge detection
        gray = cv2.cvtColor(player_region, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)

        # Find contours in the edges
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return False  # No contours, assume no cards

        # Calculate contour centers
        centers = self.calculate_contour_centers(contours)
        if len(centers) == 0:
            return False  # No centers, assume no cards

        # Apply DBSCAN clustering on the contour centers
        clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(centers)
        labels = clustering.labels_

        # Exclude noise points labeled as -1
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)

        # If clusters are found, assume cards are present (player has NOT folded)
        return n_clusters >= 1

    def detect_fold(self, frame, player_name):
        player_area = self.PLAYER_AREAS[player_name]
        # A fold is detected if no cards are present in the player's area
        return not self.detect_cards_in_area(frame, player_area)

    def run(self):
        self.running = True
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                print("Error: Failed to capture frame.")
                break

            current_player = self.active_players[self.current_player_index]

            # Detecting call/raise action in pot area
            if self.detect_movement(frame, "pot") and (time.time() - self.last_action_time) > self.cooldown_time:
                print(f"{current_player} has called/raised.")
                with self.lock:
                    self.move_history[current_player] = "called/raised"
                self.bet_opened = True  # Betting is now open
                self.last_action_time = time.time()
                # Move to the next player
                self.current_player_index = (self.current_player_index + 1) % len(self.active_players)
                continue

            # Check action: if betting is not opened, allow the current player to check
            elif not self.bet_opened and self.detect_movement(frame, current_player) and (time.time() - self.last_action_time) > self.cooldown_time:
                print(f"{current_player} has checked.")
                with self.lock:
                    self.move_history[current_player] = "checked"
                self.last_action_time = time.time()
                # Move to the next player
                self.current_player_index = (self.current_player_index + 1) % len(self.active_players)
                continue

            # Fold action: only allowed if betting has been opened
            if self.bet_opened and self.detect_fold(frame, current_player) and (time.time() - self.last_action_time) > self.cooldown_time:
                print(f"{current_player} has folded.")
                with self.lock:
                    self.move_history[current_player] = "folded"
                self.active_players.remove(current_player)
                if len(self.active_players) == 0:
                    print("All players have folded.")
                    self.running = False
                    break
                self.current_player_index %= len(self.active_players)
                self.last_action_time = time.time()
                continue

            # Add a sleep to reduce CPU usage
            time.sleep(0.01)

    def stop(self):
        self.running = False
        self.cap.release()
        
def run_yolo_model(model, frame):
    """
    Run YOLO model on a given frame and return the results.
    """
    results = model(frame, show=False)  # Run the YOLO model on the frame

    # Process results to extract information
    detections = []
    for result in results:
        boxes = result.boxes
        for box in boxes:
            cls = int(box.cls.cpu().numpy()[0])
            conf = float(box.conf.cpu().numpy()[0])
            xyxy = box.xyxy.cpu().numpy()[0].tolist()  # [x1, y1, x2, y2]
            detections.append({
                'class': cls,
                'confidence': conf,
                'bbox': xyxy  # [x1, y1, x2, y2]
            })
    return detections

@app.route('/start_move_tracking', methods=['POST'])
def start_move_tracking():
    global move_tracker
    if move_tracker is None or not move_tracker.is_alive():
        try:
            move_tracker = MoveTracker()
            move_tracker.start()
            return jsonify({'status': 'Move tracking started'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'status': 'Move tracking already running'})

@app.route('/stop_move_tracking', methods=['POST'])
def stop_move_tracking():
    global move_tracker
    if move_tracker is not None and move_tracker.is_alive():
        move_tracker.stop()
        move_tracker.join()
        move_tracker = None
        return jsonify({'status': 'Move tracking stopped'})
    else:
        return jsonify({'status': 'Move tracking is not running'})

@app.route('/get_move_history', methods=['GET'])
def get_move_history():
    global move_tracker
    if move_tracker is not None:
        with move_tracker.lock:
            move_history = move_tracker.move_history.copy()
        return jsonify({'move_history': move_history})
    else:
        return jsonify({'error': 'Move tracker is not running'}), 400

@app.route('/run_yolo', methods=['POST'])
def run_yolo():
    """
    Endpoint to run a YOLO model (chips or cards) based on AI input.
    AI should send a JSON body with 'model' set to either 'chips' or 'cards'.
    """
    global chip_model, card_model

    # Parse request data
    data = request.get_json()
    if not data or 'model' not in data:
        return jsonify({'error': 'Missing "model" parameter in request'}), 400

    model_type = data['model']
    if model_type not in ['chips', 'cards']:
        return jsonify({'error': '"model" must be either "chips" or "cards"'}), 400

    # Determine which model to use
    model = chip_model if model_type == 'chips' else card_model

    # Capture a frame
    cap = cv2.VideoCapture(1)  # Adjust camera index as needed
    if not cap.isOpened():
        return jsonify({'error': 'Unable to access the webcam'}), 500

    ret, frame = cap.read()
    cap.release()
    if not ret:
        return jsonify({'error': 'Unable to read from the webcam'}), 500

    # Run the chosen YOLO model on the frame
    detections = run_yolo_model(model, frame)
    return jsonify({'model': model_type, 'detections': detections})

if __name__ == '__main__':
    app.run(debug=True)
