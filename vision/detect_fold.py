import cv2
import numpy as np
import json
from sklearn.cluster import DBSCAN

CONFIG_FILE = "config.json"

# Load player areas from config
def load_config():
    """Loads saved player, pot, and community card locations."""
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

regions = load_config()
PLAYER_AREAS = {name: regions[name] for name in regions if "player" in name}

# Initialize webcam
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

# Read first frame for dimensions
ret, frame = cap.read()
if not ret:
    print("Error: Failed to capture initial frame.")
    cap.release()
    exit()

frame_height, frame_width = frame.shape[:2]

# Adjust bounding boxes to stay within frame limits
def adjust_bounding_box(bbox):
    x, y, w, h = bbox
    x = max(0, min(x, frame_width - 1))
    y = max(0, min(y, frame_height - 1))
    w = max(1, min(w, frame_width - x))
    h = max(1, min(h, frame_height - y))
    return (x, y, w, h)

# Apply bounding box adjustments
PLAYER_AREAS = {name: adjust_bounding_box(bbox) for name, bbox in PLAYER_AREAS.items()}

# Contour center calculation function
def calculate_contour_centers(contours):
    centers = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        center = (x + w / 2, y + h / 2)
        centers.append(center)
    return np.array(centers)

# Function to detect cards in a specific player area
def detect_cards_in_area(frame, player_area, eps=50, min_samples=1, debug=False):
    x, y, w, h = player_area
    player_region = frame[y:y+h, x:x+w]
    
    # Convert to grayscale and apply Canny edge detection
    gray = cv2.cvtColor(player_region, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    
    # Find contours in the edges
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Calculate contour centers
    centers = calculate_contour_centers(contours)
    
    # Apply DBSCAN clustering on the contour centers
    if len(centers) > 0:
        clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(centers)
        labels = clustering.labels_
        
        # Display cluster centers and count (for debugging)
        for center in centers:
            cv2.circle(player_region, (int(center[0]), int(center[1])), 5, (0, 255, 0), -1)
        
        # Count the unique clusters
        num_centers = len(set(labels)) if labels is not None else 0
        if num_centers > 0:
            return True, num_centers  # Fold detected (cards are present) and number of centers

    return False, len(centers)  # No fold detected and number of centers

print("Press 'q' to quit.")
while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Failed to capture frame.")
        break

    for player_name, player_area in PLAYER_AREAS.items():
        folded, num_centers = detect_cards_in_area(frame, player_area, debug=True)
        
        # Draw the bounding box and display the number of detected contours
        x, y, w, h = player_area
        color = (0, 0, 255) if folded else (0, 255, 0)
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        cv2.putText(frame, f"{player_name}: {num_centers} centers", (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        # Print if the player has folded (cards detected)
        if folded:
            print(f"{player_name} has folded (cards detected in area).")

    # Show the frame with bounding boxes
    cv2.imshow("Player Fold Detection", frame)

    # Exit loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

