from inference import InferencePipeline
from inference.core.interfaces.stream.sinks import render_boxes
from inference.core.interfaces.camera.entities import VideoFrame
from ..utils.shared_state import event_queue, stop_event

def hand_tracking_thread():
    """
    Uses the InferencePipeline to detect hands.
    Since the inference library insists on receiving a device integer,
    we pass the virtual camera's device index (assumed to be 1) as the video reference.
    """
    def my_custom_sink(predictions: dict, video_frame: VideoFrame):
        for p in predictions.get('predictions', []):
            event_queue.put({
                "source": "hand_tracking",
                "event": "hand_detected",
                "x": p['x'],
                "y": p['y']
            })

    def combined_sink(predictions: dict, video_frame: VideoFrame):
        render_boxes(predictions, video_frame)
        my_custom_sink(predictions, video_frame)

    virtual_cam_index = 2
    pipeline = InferencePipeline.init(
        model_id="hand_detect-xhlhk/2",  # YOLOv8x model with input size 1280
        video_reference=virtual_cam_index,
        on_prediction=combined_sink,
        api_key="cNMxZM6Ckyg2LD0DiV5n",
    )
    pipeline.start()
    pipeline.join()