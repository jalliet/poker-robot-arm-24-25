import colorsys
import numpy as np
import pyvirtualcam
import cv2

# Open camera 2
camera_2 = cv2.VideoCapture(0)  # Assuming camera 2 is at index 0

if not camera_2.isOpened():
    print("Error: Could not open camera 2.")
    exit()

with pyvirtualcam.Camera(width=640, height=480, fps=20) as cam:
    print(f'Using virtual camera: {cam.device}')
    while True:
        ret, frame = camera_2.read()
        if not ret:
            print("Error: Failed to capture frame from camera 2.")
            break

        # Display the frame from camera 2
        cv2.imshow("Camera 2 Feed", frame)

        # Send the frame to the virtual camera
        cam.send(frame)

        # Display the frame being sent to the virtual camera
        cv2.imshow("Virtual Camera Feed", frame)

        # Exit loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

camera_2.release()
cv2.destroyAllWindows()
        
