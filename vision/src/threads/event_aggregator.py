import queue

def event_aggregator_thread(event_queue, stop_event):
    while not stop_event.is_set():
        try:
            event = event_queue.get(block=True, timeout=0.5)
            # print("Event:", event)
        except queue.Empty:
            continue