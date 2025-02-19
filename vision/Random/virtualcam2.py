import cv2

def display_cameras():
    # Open the first camera device (usually device 0)
    cap1 = cv2.VideoCapture(1)
    # Open the second camera device (usually device 1)
    cap2 = cv2.VideoCapture(2)

    if not cap1.isOpened() or not cap2.isOpened():
        print("Error: Could not open one or both camera devices.")
        return

    while True:
        # Capture frame-by-frame from both cameras
        ret1, frame1 = cap1.read()
        ret2, frame2 = cap2.read()

        if not ret1 or not ret2:
            print("Error: Could not read frame from one or both cameras.")
            break

        # Display the resulting frames in separate windows
        cv2.imshow('Camera 1', frame1)
        cv2.imshow('Camera 2', frame2)

        # Press 'q' to exit the loop
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # When everything is done, release the capture and close windows
    cap1.release()
    cap2.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    display_cameras()