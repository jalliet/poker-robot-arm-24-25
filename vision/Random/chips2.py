import cv2
import os
import threading
import time
from ultralytics import YOLO  # YOLOv8

# Global variable to control the camera feed thread
camera_feed_running = True

def count_chips():
    global camera_feed_running

    # Stop the camera feed thread
    camera_feed_running = False
    time.sleep(1)  # Give some time for the thread to stop

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

    cap = cv2.VideoCapture(1)
    if not cap.isOpened():
        print("Error: Unable to access camera 1.")
        return

    ret, frame = cap.read()
    if not ret:
        print("Chip Counting: Camera feed error")
        cap.release()
        cv2.destroyAllWindows()
        return

    print("Capturing photo and counting chips...")
    results = model(frame, show=False)
    

    total_value = 0
    for result in results:
        for box in result.boxes:
            chip_class = int(box.cls.item())
            chip_color = class_to_color.get(chip_class, None)
            if chip_color and chip_color in chip_values:
                total_value += chip_values[chip_color]

    print(f"Total value of the pot: ${total_value}")

    annotated_frame = results[0].plot()
    
    # Display the annotated image in a window
    cv2.imshow("YOLO Detection", annotated_frame)
    cv2.waitKey(0)  # Wait for a key press to close the image window

    cap.release()
    cv2.destroyAllWindows()

    # Restart the camera feed thread
    camera_feed_running = True
    camera_thread = threading.Thread(target=show_camera_feed)
    camera_thread.start()

def show_camera_feed():
    global camera_feed_running

    cap = cv2.VideoCapture(1)
    if not cap.isOpened():
        print("Error: Unable to access camera 1.")
        return

    while camera_feed_running:
        ret, frame = cap.read()
        if not ret:
            print("Camera feed error")
            break

        cv2.imshow("Camera Feed", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# Start the camera feed in a separate thread
camera_thread = threading.Thread(target=show_camera_feed)
camera_thread.start()

while True:
    print("Press 'c' or 'C' to count chips from camera 1.")
    key = input().strip().lower()
    if key == 'c':
        print("Detected 'c' key press.")
        count_chips()
    elif key == 'esc':
        print("Detected 'Esc' key press. Exiting.")
        break

# Close all OpenCV windows
cv2.destroyAllWindows()
