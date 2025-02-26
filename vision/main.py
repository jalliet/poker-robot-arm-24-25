import cv2
import time
import threading
from src.utils.shared_state import stop_event
from src.threads.birds_eye_camera import birds_eye_camera_thread
from src.threads.chip_detection import chip_detection_thread
from src.threads.fold_detection import fold_detection_thread
from src.threads.hand_tracking import hand_tracking_thread
from src.threads.key_listener import key_listener_thread
from src.threads.event_aggregator import event_aggregator_thread

def main():
    threads = []

    # 1. Birds-Eye Camera Thread (Producer):
    birds_eye_thread = threading.Thread(target=birds_eye_camera_thread, name="BirdsEyeCamera", daemon=True)
    threads.append(birds_eye_thread)

    # 2. Chip Detection Thread (Triggered on Demand):
    chip_thread = threading.Thread(target=chip_detection_thread, name="ChipDetection", daemon=True)
    threads.append(chip_thread)

    # 3. Fold Detection Thread (Consumer):
    fold_thread = threading.Thread(target=fold_detection_thread, name="FoldDetection", daemon=True)
    threads.append(fold_thread)

    # 4. Hand Tracking Thread (Uses the virtual cam device index):
    hand_thread = threading.Thread(target=hand_tracking_thread, name="HandTracking", daemon=True)
    threads.append(hand_thread)

    # 5. Event Aggregator Thread:
    aggregator_thread = threading.Thread(target=event_aggregator_thread, name="Aggregator", daemon=True)
    threads.append(aggregator_thread)

    # 6. Key Listener Thread:
    key_thread = threading.Thread(target=key_listener_thread, name="KeyListener", daemon=True)
    threads.append(key_thread)

    # Start all threads.
    for t in threads:
        t.start()
    print("All threads started. Press Ctrl+C or 'q' in the console to exit.")

    try:
        while not stop_event.is_set():
            time.sleep(0.1)
    except KeyboardInterrupt:
        stop_event.set()
        print("KeyboardInterrupt detected, exiting.")

    for t in threads:
        t.join()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()