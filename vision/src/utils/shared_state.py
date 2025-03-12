import queue
import threading

# Shared state for all threads
shared_frame = {"birds_eye": None}
birds_eye_lock = threading.Lock()
event_queue = queue.Queue()
stop_event = threading.Event()
chip_detection_event = threading.Event()