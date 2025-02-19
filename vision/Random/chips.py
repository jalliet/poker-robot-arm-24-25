import cv2
import torch
from ultralytics import YOLO  # YOLOv8
import os

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
model = YOLO("vision/chips_train/train/weights/best.pt")

# List of sample images
image_folder = "vision/sample_images"
image_files = [f"chips{i}.jpg" for i in range(1, 6)]
print(image_files)

# Function to process an image and calculate the total pot value
def process_image(image):
    results = model(image, show=False)
    detected_classes = set()
    for result in results:
        for box in result.boxes:
            detected_classes.add(int(box.cls.item()))  # Convert tensor to integer
    print(f"Detected classes: {detected_classes}")

    total_value = 0
    for result in results:
        for box in result.boxes:
            chip_class = int(box.cls.item())  # Convert tensor to integer
            chip_color = class_to_color.get(chip_class, None)  # Map class to color
            if chip_color and chip_color in chip_values:
                total_value += chip_values[chip_color]

    print(f"Total value of the pot: ${total_value}")

    annotated_image = results[0].plot()
    resized_image = cv2.resize(annotated_image, (800, 600))  # Resize to 800x600
    cv2.imshow("YOLO Detection - Camera", resized_image)
    cv2.waitKey(0)  # Wait for a key press to close the image window

# Process each image
index = 0
while index < len(image_files):
    image_file = image_files[index]
    image_path = os.path.join(image_folder, image_file)
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Unable to read image {image_file}.")
        index += 1
        continue

    # Run YOLO model on the image
    results = model(image, show=False)

    # Print all detected classes
    detected_classes = set()
    for result in results:
        for box in result.boxes:
            detected_classes.add(int(box.cls.item()))  # Convert tensor to integer
    print(f"Detected classes in {image_file}: {detected_classes}")

    # Calculate the total value of the pot
    total_value = 0
    for result in results:
        for box in result.boxes:
            chip_class = int(box.cls.item())  # Convert tensor to integer
            chip_color = class_to_color.get(chip_class, None)  # Map class to color
            if chip_color and chip_color in chip_values:
                total_value += chip_values[chip_color]

    print(f"Total value of the pot in {image_file}: ${total_value}")

    # Draw bounding boxes on the image
    annotated_image = results[0].plot()

    # Resize the image window
    resized_image = cv2.resize(annotated_image, (800, 600))  # Resize to 800x600

    # Show the image with detections
    cv2.imshow(f"YOLO Detection - {image_file}", resized_image)
    cv2.waitKey(0)  # Wait for a key press to close the image window
    index += 1

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

    cap = cv2.VideoCapture(1)
    if not cap.isOpened():
        print("Error: Unable to access camera 1.")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Chip Counting: Camera feed error")
            break

        cv2.imshow("Camera 1 Feed", frame)
        key = cv2.waitKey(1) & 0xFF

        if key in [ord('c'), ord('C')]:
            print("Key 'c' pressed. Capturing photo and counting chips...")
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
            cv2.imshow("YOLO Detection", annotated_frame)
            cv2.waitKey(0)  # Wait for a key press to close the image window
            break

    cap.release()
    cv2.destroyAllWindows()

# Capture image from camera 1 when 'c' or 'C' is pressed
print("Press 'c' or 'C' to capture an image from camera 1.")
while True:
    key = cv2.waitKey(1) & 0xFF
    if key in [ord('c'), ord('C')]:
        count_chips()
    elif key == 27:  # Press 'Esc' to exit
        break

# Close all OpenCV windows
cv2.destroyAllWindows()