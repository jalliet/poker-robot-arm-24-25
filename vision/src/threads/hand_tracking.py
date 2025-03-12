from inference import InferencePipeline
from inference.core.interfaces.stream.sinks import render_boxes
from inference.core.interfaces.camera.entities import VideoFrame
import os
import json
import cv2
from dotenv import load_dotenv

def hand_tracking_thread(event_queue, stop_event):
    
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

    # Load player areas from config.json
    CONFIG_FILE = "vision/config.json"
    try:
        with open(CONFIG_FILE, "r") as f:
            regions = json.load(f)
            
        # Extract player areas from config
        PLAYER_AREAS = {name: regions[name] for name in regions 
                        if "player" in name and isinstance(regions[name], list) and len(regions[name]) == 4}
        
        print(f"Loaded player areas: {PLAYER_AREAS}")
        
    except Exception as e:
        event_queue.put({
            "source": "hand_tracking",
            "event": "error",
            "message": f"Failed to load config: {e}"
        })
        return

    def is_point_in_area(x, y, area):
        """Check if a point (x, y) is inside a rectangular area [x, y, w, h]"""
        area_x, area_y, area_w, area_h = area
        return (area_x <= x <= area_x + area_w) and (area_y <= y <= area_y + area_h)

    def get_player_from_coordinates(x, y):
        """Determine which player area contains the given coordinates"""
        for player_name, area in PLAYER_AREAS.items():
            if is_point_in_area(x, y, area):
                return player_name
        return None

    def my_custom_sink(predictions: dict, video_frame: VideoFrame):
        for p in predictions.get('predictions', []):
            x, y = p['x'], p['y']
            player_name = get_player_from_coordinates(x, y)
            
            if player_name:
                print(f"Hand detected in {player_name} area at coordinates ({x}, {y})")
                event_queue.put({
                    "source": "hand_tracking",
                    "event": "hand_detected",
                    "player_name": player_name,
                    "x": x,
                    "y": y
                })
            else:
                # Hand detected but not in any player area
                print(f"Hand detected outside player areas at coordinates ({x}, {y})")
        
    def combined_sink(predictions: dict, video_frame: VideoFrame):
        # Render boxes on the video frame
        render_boxes(predictions, video_frame, annotator=None, display_size=(640,480))
        
        # Process hand detections for event queue
        my_custom_sink(predictions, video_frame)

    virtual_cam_index = 2
    
    pipeline = InferencePipeline.init(
        model_id="hand_detect-xhlhk/2",
        video_reference=virtual_cam_index,
        on_prediction=combined_sink,
        api_key=api_key,
        video_source_properties={"frame_width": 640.0, "frame_height": 480.0}
    )
    
    print("Hand tracking thread started")
    
    try:
        pipeline.start()
        
        # Wait for stop event
        while not stop_event.is_set():
            import time
            time.sleep(0.1)
            
        # Stop the pipeline when stop event is set
        pipeline.stop()
    except Exception as e:
        event_queue.put({
            "source": "hand_tracking",
            "event": "error",
            "message": f"Pipeline error: {e}"
        })
    finally:
        print("Hand tracking thread stopped")