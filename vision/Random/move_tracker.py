import cv2
import numpy as np
import time
from sklearn.cluster import DBSCAN
import json

CONFIG_FILE = "config.json"

def load_config():
    """Loads saved player, pot, and community card locations."""
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

regions = load_config()
print("Loaded Configuration:", regions)


active_players = ["player_1", "player_2", "player_3", "player_4"]
current_player_index = 0
move_history = {player: None for player in active_players}

# Initialize webcam
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

# Read the first frame to get frame dimensions
ret, frame = cap.read()
if not ret:
    print("Error: Failed to capture initial frame.")
    cap.release()
    exit()

frame_height, frame_width = frame.shape[:2]
print(f"Frame dimensions: Width={frame_width}, Height={frame_height}")

# Verify and adjust bounding boxes if necessary
def adjust_bounding_box(area_name, bbox):
    x, y, w, h = bbox
    x = max(0, min(x, frame_width - 1))
    y = max(0, min(y, frame_height - 1))
    w = max(1, min(w, frame_width - x))
    h = max(1, min(h, frame_height - y))
    return (x, y, w, h)

POT_AREA = adjust_bounding_box("pot", POT_AREA)
PLAYER_AREAS = {name: adjust_bounding_box(name, bbox) for name, bbox in PLAYER_AREAS.items()}

# Initialize motion tracking information for each area
AREAS = {"pot": POT_AREA}
AREAS.update(PLAYER_AREAS)

motion_info = {}
for area in AREAS.keys():
    motion_info[area] = {
        "fgbg": cv2.createBackgroundSubtractorMOG2(),
        "last_mean": 0.0,
        "motion_detected_time": 0.0
    }

cooldown_time = 3.0
bet_opened = False  # Indicates if a call/raise has occurred
last_action_time = time.time()

print("Press spacebar to end the round.")

def detect_movement(frame, area_name):
    x, y, w, h = AREAS[area_name]
    roi = frame[y:y + h, x:x + w]
    fgbg = motion_info[area_name]["fgbg"]
    fgmask = fgbg.apply(roi)

    current_mean = np.mean(fgmask)
    result = abs(current_mean - motion_info[area_name]["last_mean"])
    motion_info[area_name]["last_mean"] = current_mean

    threshold = 0.5  # Adjust as needed
    if result > threshold and (time.time() - motion_info[area_name]["motion_detected_time"]) > cooldown_time:
        motion_info[area_name]["motion_detected_time"] = time.time()
        return True
    else:
        return False

def detect_cards_in_area(frame, player_area, eps=50, min_samples=1, debug=False):
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
    centers = calculate_contour_centers(contours)
    if len(centers) == 0:
        return False  # No centers, assume no cards

    # Apply DBSCAN clustering on the contour centers
    clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(centers)
    labels = clustering.labels_

    # Exclude noise points labeled as -1
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)

    # If clusters are found, assume cards are present (player has NOT folded)
    # return n_clusters >= 2
    return False

def calculate_contour_centers(contours):
    centers = []
    for cnt in contours:
        M = cv2.moments(cnt)
        if M["m00"] != 0:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            centers.append([cX, cY])
    return np.array(centers)

def detect_fold(frame, player_name):
    player_area = PLAYER_AREAS[player_name]
    # A fold is detected if no cards are present in the player's area
    return not detect_cards_in_area(frame, player_area)

# Main loop
while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Failed to capture frame.")
        break

    # Display the current active player
    current_player = active_players[current_player_index]
    cv2.putText(frame, f"Current Player: {current_player}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    # Draw bounding boxes for each player area
    for player, (x, y, w, h) in PLAYER_AREAS.items():
        color = (0, 255, 0) if player == current_player else (255, 0, 0)
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        cv2.putText(frame, player, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

    # Draw bounding box for the pot area
    x, y, w, h = POT_AREA
    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 2)
    cv2.putText(frame, "Pot", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

    # Detecting call/raise action in pot area
    if detect_movement(frame, "pot") and (time.time() - last_action_time) > cooldown_time:
        print(f"{current_player} has called/raised.")
        move_history[current_player] = "called/raised"
        bet_opened = True  # Betting is now open
        last_action_time = time.time()
        # Move to the next player
        current_player_index = (current_player_index + 1) % len(active_players)
        continue

    # Check action: if betting is not opened, allow the current player to check
    elif not bet_opened and detect_movement(frame, current_player) and (time.time() - last_action_time) > cooldown_time:
        print(f"{current_player} has checked.")
        move_history[current_player] = "checked"
        last_action_time = time.time()
        # Move to the next player
        current_player_index = (current_player_index + 1) % len(active_players)
        continue

    # Fold action: only allowed if betting has been opened
    if bet_opened and detect_fold(frame, current_player) and (time.time() - last_action_time) > cooldown_time:
        print(f"{current_player} has folded.")
        move_history[current_player] = "folded"
        active_players.remove(current_player)
        if len(active_players) == 0:
            print("All players have folded.")
            break
        current_player_index %= len(active_players)
        last_action_time = time.time()
        continue

    # Display the frame with the current player and detected actions
    cv2.imshow("Poker Tracker", frame)

    # End round on spacebar press
    if cv2.waitKey(1) & 0xFF == ord(' '):
        print("Round ended.")
        break

# Print move history at the end
print("\nMove History:")
for player, move in move_history.items():
    print(f"{player}: {move}")

cap.release()
cv2.destroyAllWindows()

