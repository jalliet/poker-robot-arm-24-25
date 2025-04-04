from inference import InferencePipeline
from inference.core.interfaces.stream.sinks import render_boxes
from inference.core.interfaces.camera.entities import VideoFrame
from dotenv import load_dotenv
import os

def hand_tracking_thread(event_queue, stop_event):

    # Load environment variables
    load_dotenv()
    
    # Get API key from environment variable
    api_key = os.getenv("INFERENCE_API_KEY")
    
    if not api_key:
        event_queue.put({
            "source": "hand_tracking",
            "event": "error",
            "message": "INFERENCE_API_KEY environment variable not set"
        })
        return
    
    def my_custom_sink(predictions: dict, video_frame: VideoFrame):
        for p in predictions.get('predictions', []):
            event_queue.put({
                "source": "hand_tracking",
                "event": "hand_detected",
                "x": p['x'],
                "y": p['y']
            })
        
    def combined_sink(predictions: dict, video_frame: VideoFrame):
        render_boxes(predictions, video_frame, annotator=None, display_size=(640,480))
        my_custom_sink(predictions, video_frame)

    virtual_cam_index = 2
    
    pipeline = InferencePipeline.init(
        model_id="hand_detect-xhlhk/2",
        video_reference=virtual_cam_index,
        on_prediction=combined_sink,
        api_key="cNMxZM6Ckyg2LD0DiV5n",
        video_source_properties={"frame_width": 640.0, "frame_height": 480.0}
    )
    
    pipeline.start()
    pipeline.join()