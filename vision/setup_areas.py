import cv2
import json
import os

# File to store the configuration
CONFIG_FILE = "config.json"

# Default regions if no config file exists
default_regions = {
    "player_1": [100, 200, 150, 150],
    "player_2": [300, 200, 150, 150],
    "player_3": [500, 200, 150, 150],
    "player_4": [700, 200, 150, 150],
    "pot_area": [400, 400, 200, 200],
    "community_cards": [300, 100, 400, 150]
}

# Load existing configuration (or default if missing)
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as f:
        regions = json.load(f)
else:
    regions = default_regions.copy()

# Initialize video feed
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

# Interaction states
selected_region = None
dragging = False
resizing = False
offset_x, offset_y = 0, 0
resize_corner = None

# Define function to check if point is inside a rectangle
def inside_region(x, y, rect):
    rx, ry, rw, rh = rect
    return rx <= x <= rx + rw and ry <= y <= ry + rh

# Mouse callback function
def mouse_callback(event, x, y, flags, param):
    global selected_region, dragging, offset_x, offset_y, resizing, resize_corner

    if event == cv2.EVENT_LBUTTONDOWN:
        for key, (rx, ry, rw, rh) in regions.items():
            # Check if clicking near a corner for resizing
            corners = {
                "top-left": (rx, ry),
                "top-right": (rx + rw, ry),
                "bottom-left": (rx, ry + rh),
                "bottom-right": (rx + rw, ry + rh)
            }
            for corner, (cx, cy) in corners.items():
                if abs(x - cx) < 10 and abs(y - cy) < 10:
                    selected_region = key
                    resizing = True
                    resize_corner = corner
                    return
            
            # If not resizing, check if clicking inside the region
            if inside_region(x, y, (rx, ry, rw, rh)):
                selected_region = key
                dragging = True
                offset_x, offset_y = x - rx, y - ry
                return

    elif event == cv2.EVENT_MOUSEMOVE:
        if dragging and selected_region:
            # Move the region by updating its top-left corner
            rx, ry, rw, rh = regions[selected_region]
            regions[selected_region] = [x - offset_x, y - offset_y, rw, rh]

        if resizing and selected_region:
            rx, ry, rw, rh = regions[selected_region]
            if resize_corner == "top-left":
                regions[selected_region] = [x, y, rx + rw - x, ry + rh - y]
            elif resize_corner == "top-right":
                regions[selected_region] = [rx, y, x - rx, ry + rh - y]
            elif resize_corner == "bottom-left":
                regions[selected_region] = [x, ry, rx + rw - x, y - ry]
            elif resize_corner == "bottom-right":
                regions[selected_region] = [rx, ry, x - rx, y - ry]

    elif event == cv2.EVENT_LBUTTONUP:
        dragging = False
        resizing = False
        resize_corner = None

# Save and exit
def save_and_exit():
    with open(CONFIG_FILE, "w") as f:
        json.dump(regions, f, indent=4)
    print("Configuration saved!")
    cap.release()
    cv2.destroyAllWindows()
    exit()

# Set up OpenCV window
cv2.namedWindow("Setup Regions")
cv2.setMouseCallback("Setup Regions", mouse_callback)

print("Instructions:")
print("- Left-click **inside a region** to move it")
print("- Left-click **on a corner** to resize")
print("- Press **Enter** to save changes and exit")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Draw all regions
    for key, (x, y, w, h) in regions.items():
        color = (0, 255, 0) if "player" in key else (255, 0, 0)
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        cv2.putText(frame, key, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        # Draw small circles on corners for resizing
        for cx, cy in [(x, y), (x + w, y), (x, y + h), (x + w, y + h)]:
            cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)

    cv2.imshow("Setup Regions", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == 13:  # Enter key
        save_and_exit()
    elif key == ord("q"):  # Quit without saving
        cap.release()
        cv2.destroyAllWindows()
        exit()

