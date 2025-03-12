import json
import time
import cv2
import threading
import queue
import numpy as np

def fold_detection_thread(shared_frame, birds_eye_lock, event_queue, stop_event):
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

    PLAYER_AREAS = {name: regions[name] for name in regions 
                    if "player" in name and isinstance(regions[name], list) and len(regions[name]) == 4}

    while shared_frame["birds_eye"] is None and not stop_event.is_set():
        time.sleep(0.01)
    with birds_eye_lock:
        frame = shared_frame["birds_eye"].copy()
    frame_height, frame_width = frame.shape[:2]

    def adjust_bounding_box(bbox):
        x, y, w, h = [int(val) for val in bbox]
        x = max(0, min(x, frame_width - 1))
        y = max(0, min(y, frame_height - 1))
        w = max(1, min(w, frame_width - x))
        h = max(1, min(h, frame_height - y))
        return (x, y, w, h)

    PLAYER_AREAS = {name: adjust_bounding_box(bbox) for name, bbox in PLAYER_AREAS.items()}

    def detect_red_area(frame, player_area):
        x, y, w, h = player_area
        player_region = frame[y:y+h, x:x+w]
        
        hsv = cv2.cvtColor(player_region, cv2.COLOR_BGR2HSV)
        
        lower_red1 = np.array([0, 70, 70])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([160, 70, 70])
        upper_red2 = np.array([180, 255, 255])
        
        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask = cv2.bitwise_or(mask1, mask2)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            largest_contour = max(contours, key=cv2.contourArea, default=None)
            if largest_contour is not None:
                area = cv2.contourArea(largest_contour)
                SINGLE_CARD_AREA = 800
                if area > SINGLE_CARD_AREA * 0.5:
                    return True, area
        return False, 0

    consecutive_folding_counts = {player: 0 for player in PLAYER_AREAS.keys()}
    FOLD_THRESHOLD = 50

    print("Press 'q' to quit. Players: Place a single red card face down to fold.")
    while not stop_event.is_set():
        with birds_eye_lock:
            if shared_frame["birds_eye"] is None:
                continue
            frame = shared_frame["birds_eye"].copy()

        folded_players = []
        for player_name, player_area in PLAYER_AREAS.items():
            folded, area = detect_red_area(frame, player_area)
            if folded:
                consecutive_folding_counts[player_name] += 1
            else:
                consecutive_folding_counts[player_name] = 0
            is_folded = consecutive_folding_counts[player_name] >= FOLD_THRESHOLD

            x, y, w, h = player_area
            color = (0, 0, 255) if is_folded else (0, 255, 0)
            label = f"{player_name}: {'Folded' if is_folded else 'Active'}"
            if is_folded:
                folded_players.append(player_name)
                # Send fold event to the event queue
                event_queue.put({
                    "source": "fold_detection",
                    "event": "fold",
                    "player_name": player_name,
                    "timestamp": time.time()
                })
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        if folded_players:
            print(f"Folded players: {', '.join(folded_players)}")

        cv2.imshow("Fold Detection", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            stop_event.set()
            break
        time.sleep(0.01)
    cv2.destroyWindow("Fold Detection")