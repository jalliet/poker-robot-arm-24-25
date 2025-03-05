import cv2
import pyvirtualcam
import threading
import queue

def birds_eye_camera_thread(shared_frame, birds_eye_lock, event_queue, stop_event):
    physical_cam_index = 0
    cap = cv2.VideoCapture(physical_cam_index)
    if not cap.isOpened():
        event_queue.put({
            "source": "birds_eye_camera",
            "event": "error",
            "message": f"Unable to open physical camera (index {physical_cam_index})."
        })
        return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480
    fps = cap.get(cv2.CAP_PROP_FPS) or 20

    print(f"Camera properties - Width: {width}, Height: {height}, FPS: {fps}")

    try:
        with pyvirtualcam.Camera(width=width, height=height, fps=fps) as virtual_cam:
            print(f"Virtual camera created: {virtual_cam.device}")
            while not stop_event.is_set():
                ret, frame = cap.read()
                if not ret:
                    event_queue.put({
                        "source": "birds_eye_camera",
                        "event": "error",
                        "message": "Failed to capture frame from physical camera."
                    })
                    break

                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                virtual_cam.send(rgb_frame)
                virtual_cam.sleep_until_next_frame()

                with birds_eye_lock:
                    shared_frame["birds_eye"] = frame.copy()

                cv2.imshow("Physical Camera Feed", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    stop_event.set()
                    break

    except Exception as e:
        event_queue.put({
            "source": "birds_eye_camera",
            "event": "error",
            "message": f"Virtual camera error: {e}"
        })
    finally:
        cap.release()
        cv2.destroyWindow("Physical Camera Feed")