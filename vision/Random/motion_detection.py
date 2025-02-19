'''
import cv2
import numpy as np
import time

# Initialize webcam
cap = cv2.VideoCapture(1)

# Optionally, set the resolution (uncomment and adjust if needed)
# cap.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
# cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)

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

# Define all areas (pot and players) with their bounding boxes
# Ensure that all bounding boxes are within the frame dimensions
AREAS = {
    "pot": (0, 25, 600, 100),          # (x, y, width, height)
    "player_area": (0, 325, 600, 150),
}

# Verify and adjust bounding boxes if necessary
for area_name, (x, y, w, h) in AREAS.items():
    if x + w > frame_width or y + h > frame_height:
        print(f"Warning: {area_name} bounding box exceeds frame dimensions. Adjusting...")
        w = min(w, frame_width - x)
        h = min(h, frame_height - y)
        AREAS[area_name] = (x, y, w, h)
        print(f"Adjusted {area_name}: (x={x}, y={y}, w={w}, h={h})")

# Initialize motion tracking information for each area
motion_info = {}
for area in AREAS.keys():
    motion_info[area] = {
        "fgbg": cv2.createBackgroundSubtractorMOG2(),
        "last_mean": 0.0,
        "motion_detected_time": 0.0,
        "last_frame": None
    }

start_time = time.time()  # Record the start time
initial_delay = 5  # Initial delay in seconds

cooldown = 5.0  # Cooldown period in seconds
threshold = 12.0  # Motion detection threshold (adjust based on testing)

player_motion_detected_time = 0.0  # Time when motion was detected in the player area
player_to_pot_delay = 2.0  # Delay in seconds to check for pot motion after player motion

print("Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Failed to capture frame.")
        break

    # Apply Gaussian blur to reduce noise
    frame_blurred = cv2.GaussianBlur(frame, (21, 21), 0)

    # Skip motion detection during the initial delay period
    if time.time() - start_time < initial_delay:
        cv2.imshow('Motion Detector', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Exiting...")
            break
        continue

    max_motion = 0
    max_motion_area = None
    pot_motion_detected = False

    # Iterate through all defined areas
    for area_name, (x, y, w, h) in AREAS.items():
        # Draw bounding box for the area
        if area_name == "pot":
            color = (0, 255, 0)  # Green for pot
        else:
            color = (255, 0, 0)  # Blue for players
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        cv2.putText(frame, area_name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, color, 1, cv2.LINE_AA)

        # Extract the region of interest (ROI) for motion detection
        roi = frame_blurred[y:y + h, x:x + w]

        # Apply background subtraction to the ROI
        fgmask = motion_info[area_name]["fgbg"].apply(roi)

        # Apply Gaussian blur to the foreground mask to reduce noise
        fgmask_blurred = cv2.GaussianBlur(fgmask, (21, 21), 0)

        # Calculate the mean value of the foreground mask
        current_mean = np.mean(fgmask_blurred)
        result = abs(current_mean - motion_info[area_name]["last_mean"])
        motion_info[area_name]["last_mean"] = current_mean

        # Check if motion is detected and cooldown has passed
        if result > threshold and (time.time() - motion_info[area_name]["motion_detected_time"]) > cooldown:
            if area_name == "player_area":
                player_motion_detected_time = time.time()
                max_motion_area = area_name
            elif area_name == "pot" and (time.time() - player_motion_detected_time) <= player_to_pot_delay:
                pot_motion_detected = True
                max_motion_area = area_name
                break  # Prioritize pot motion if detected within the delay period
            elif result > max_motion:
                max_motion = result
                max_motion_area = area_name

    # Check if the delay period has passed without detecting pot motion
    if max_motion_area == "player_area" and (time.time() - player_motion_detected_time) > player_to_pot_delay:
        print(f"Motion detected in player_area after delay!")
        motion_info[max_motion_area]["motion_detected_time"] = time.time()
        max_motion_area = None  # Reset max_motion_area to avoid reprocessing

    if max_motion_area:
        x, y, w, h = AREAS[max_motion_area]
        print(f"Motion detected in {max_motion_area}!")
        motion_info[max_motion_area]["motion_detected_time"] = time.time()

        # Optional: Change the color of the bounding box to indicate motion
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
        cv2.putText(frame, f"Motion in {max_motion_area}", (x, y + h + 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2, cv2.LINE_AA)

    # Display the frame with bounding boxes
    cv2.imshow('Motion Detector', frame)

    # Exit when 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("Exiting...")
        break

# Release resources
cap.release()
cv2.destroyAllWindows()
'''
import cv2
import numpy as np
import time

# Initialize webcam
cap = cv2.VideoCapture(1)

# Check if the camera opened successfully
if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

# Initialize the Kalman Filter for tracking motion
kalman = cv2.KalmanFilter(4, 2)
kalman.measurementMatrix = np.array([[1, 0, 0, 0],
                                     [0, 1, 0, 0]], np.float32)
kalman.transitionMatrix = np.array([[1, 0, 1, 0],
                                    [0, 1, 0, 1],
                                    [0, 0, 1, 0],
                                    [0, 0, 0, 1]], np.float32)
kalman.processNoiseCov = np.eye(4, dtype=np.float32) * 0.03

# Background subtractor
fgbg = cv2.createBackgroundSubtractorMOG2()

print("Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Failed to capture frame.")
        break

    # Apply Gaussian blur
    frame_blurred = cv2.GaussianBlur(frame, (21, 21), 0)

    # Apply background subtraction
    fgmask = fgbg.apply(frame_blurred)

    # Apply morphological operations to clean noise
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    fgmask_cleaned = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel)

    # Find contours of the moving objects
    contours, _ = cv2.findContours(fgmask_cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        if cv2.contourArea(contour) > 500:  # Filter small movements
            x, y, w, h = cv2.boundingRect(contour)
            
            # Update Kalman Filter with the detected position
            measurement = np.array([[np.float32(x + w // 2)], [np.float32(y + h // 2)]])
            kalman.correct(measurement)
            prediction = kalman.predict()

            # Draw bounding box
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.circle(frame, (int(prediction[0][0]), int(prediction[1][0])), 4, (0, 0, 255), -1)

    # Display the frame
    cv2.imshow('Motion Detector', frame)

    # Exit when 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("Exiting...")
        break

# Release resources
cap.release()
cv2.destroyAllWindows()
