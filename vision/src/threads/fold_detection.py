import cv2
import json
import time
import numpy as np
from sklearn.cluster import DBSCAN
from ..utils.shared_state import shared_frame, birds_eye_lock, event_queue, stop_event

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

    PLAYER_AREAS = {name: regions[name] for name in regions if "player" in name}

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