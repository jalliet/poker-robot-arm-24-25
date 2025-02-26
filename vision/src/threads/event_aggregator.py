import queue
from ..utils.shared_state import event_queue, stop_event

def event_aggregator_thread():
    """
    Aggregates and (optionally) prints events from various threads.
    """
    while not stop_event.is_set():
        try:
            event = event_queue.get(timeout=0.5)
            # print("Event:", event)
        except queue.Empty:
            continue