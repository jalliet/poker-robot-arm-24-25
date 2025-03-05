import threading
import time
import queue
import cv2

shared_frame = {"birds_eye": None}
birds_eye_lock = threading.Lock()
event_queue = queue.Queue()
stop_event = threading.Event()
chip_detection_event = threading.Event()

from src.threads.birds_eye_camera import birds_eye_camera_thread
from src.threads.chip_detection import chip_detection_thread
from src.threads.event_aggregator import event_aggregator_thread
from src.threads.fold_detection import fold_detection_thread
from src.threads.hand_tracking import hand_tracking_thread
from src.threads.key_listener import key_listener_thread

def main():
    threads = []

    birds_eye_thread = threading.Thread(target=birds_eye_camera_thread, args=(shared_frame, birds_eye_lock, event_queue, stop_event), name="BirdsEyeCamera", daemon=True)
    threads.append(birds_eye_thread)

    chip_thread = threading.Thread(target=chip_detection_thread, args=(event_queue, stop_event, chip_detection_event), name="ChipDetection", daemon=True)
    threads.append(chip_thread)

    fold_thread = threading.Thread(target=fold_detection_thread, args=(shared_frame, birds_eye_lock, event_queue, stop_event), name="FoldDetection", daemon=True)
    threads.append(fold_thread)

    hand_thread = threading.Thread(target=hand_tracking_thread, args=(event_queue, stop_event), name="HandTracking", daemon=True)
    threads.append(hand_thread)

    aggregator_thread = threading.Thread(target=event_aggregator_thread, args=(event_queue, stop_event), name="Aggregator", daemon=True)
    threads.append(aggregator_thread)

    key_thread = threading.Thread(target=key_listener_thread, args=(stop_event, chip_detection_event), name="KeyListener", daemon=True)
    threads.append(key_thread)

    for t in threads:
        t.start()
    print("All threads started. Press Ctrl+C or 'q' in the console to exit.")

    try:
        while not stop_event.is_set():
            time.sleep(0.01)
    except KeyboardInterrupt:
        stop_event.set()
        print("KeyboardInterrupt detected, exiting.")

    for t in threads:
        t.join()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()