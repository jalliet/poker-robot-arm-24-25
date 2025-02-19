import cv2
import torch
from ultralytics import YOLO  # YOLOv8

# Load the YOLO model
model = YOLO("vision/train/train/weights/best.pt") 

# Start webcam capture
cap = cv2.VideoCapture(1) 
if not cap.isOpened():
    print("Error: Unable to access the webcam.")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Unable to read from the webcam.")
        break

    # Run YOLO model on the frame
    results = model(frame, show=False)  

    # Draw bounding boxes on the frame
    annotated_frame = results[0].plot()  

    # Show the frame with detections
    cv2.imshow("YOLO Detection", annotated_frame)

    # Break the loop on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()
