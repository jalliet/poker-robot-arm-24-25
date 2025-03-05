import time

def key_listener_thread(stop_event, chip_detection_event):
    while not stop_event.is_set():
        user_input = input("Press 'c' to count chips (or 'q' to quit): ").strip().lower()
        if user_input == 'c':
            chip_detection_event.set()
        elif user_input in ['q', 'esc']:
            stop_event.set()
            break
        time.sleep(0.01)