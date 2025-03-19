from inference import InferencePipeline
from inference.core.interfaces.stream.sinks import render_boxes
from inference.core.interfaces.camera.entities import VideoFrame
import os
import json
import cv2
import time
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

    # Dict to track hand positions over time for each player
    hand_tracking_data = {player_name: {
        "last_position": None,      # Last detected position (x, y)
        "start_time": 0,            # When hand started holding still
        "is_stable": False,         # Whether hand is currently stable
        "check_triggered": False,   # Whether check has been triggered for current stable position
        "recent_positions": [],     # Store recent positions for smoothing
        "current_distance": 0       # Current stability distance for debugging
    } for player_name in PLAYER_AREAS.keys()}
    
    # Constants for hand stability detection
    STABILITY_THRESHOLD = 150      # Maximum movement distance (pixels) to consider hand stable
    HOLD_DURATION = 1.0             # Time in seconds hand must be held still to trigger check
    POSITIONS_HISTORY = 5           # Number of recent positions to keep for smoothing

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
    
    def hand_distance(pos1, pos2):
        """Calculate Euclidean distance between two hand positions"""
        if not pos1 or not pos2:
            return float('inf')
        return ((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)**0.5

    def my_custom_sink(predictions: dict, video_frame: VideoFrame):
        # Use global time module instead of trying to access it from enclosing scope
        current_time = time.time()
        
        # Track detected hands by player area
        detected_in_area = set()
        
        # Get the actual frame to draw on
        frame = video_frame.image
        
        for p in predictions.get('predictions', []):
            x, y = p['x'], p['y']
            player_name = get_player_from_coordinates(x, y)
            
            if player_name:
                detected_in_area.add(player_name)
                print(f"Hand detected in {player_name} area at coordinates ({x}, {y})")
                
                # Get tracking data for this player
                track_data = hand_tracking_data[player_name]
                last_pos = track_data["last_position"]
                
                # Update position and check stability
                if last_pos is None:
                    # First detection, initialize tracking
                    track_data["last_position"] = (x, y)
                    track_data["start_time"] = current_time
                    track_data["is_stable"] = True
                    track_data["check_triggered"] = False
                    track_data["recent_positions"] = [(x, y)]
                    track_data["current_distance"] = 0
                else:
                    # Add current position to recent positions list (for smoothing)
                    track_data["recent_positions"].append((x, y))
                    
                    # Keep only the most recent positions
                    if len(track_data["recent_positions"]) > POSITIONS_HISTORY:
                        track_data["recent_positions"] = track_data["recent_positions"][-POSITIONS_HISTORY:]
                    
                    # Get smoothed position (average of recent positions)
                    avg_x = sum(p[0] for p in track_data["recent_positions"]) / len(track_data["recent_positions"])
                    avg_y = sum(p[1] for p in track_data["recent_positions"]) / len(track_data["recent_positions"])
                    
                    # Calculate distance from last known position to smoothed position
                    distance = hand_distance((avg_x, avg_y), last_pos)
                    track_data["current_distance"] = distance
                    
                    if distance <= STABILITY_THRESHOLD:
                        # Hand is stable
                        if not track_data["is_stable"]:
                            # Hand just became stable, reset timer
                            track_data["start_time"] = current_time
                            track_data["is_stable"] = True
                        
                        # Check if hand has been stable for required duration
                        stable_duration = current_time - track_data["start_time"]
                        
                        # Calculate progress percentage (0-100%)
                        progress_pct = min(100, int((stable_duration / HOLD_DURATION) * 100))
                        
                        # Print feedback about stability progress
                        if progress_pct % 25 == 0 and not track_data["check_triggered"]:
                            print(f"{player_name} hand stable: {progress_pct}% towards CHECK")
                        
                        # Draw progress bar above hand position
                        if frame is not None and not track_data["check_triggered"]:
                            # Progress bar dimensions - MAKE IT LARGER AND MORE VISIBLE
                            bar_width = 150
                            bar_height = 25
                            bar_x = int(x) - bar_width // 2
                            bar_y = int(y) - 60  # Show bar above the hand
                            
                            # Draw progress bar background (gray)
                            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), 
                                        (100, 100, 100), -1)
                            
                            # Draw progress bar fill (bright blue) based on progress
                            fill_width = int((progress_pct / 100.0) * bar_width)
                            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill_width, bar_y + bar_height), 
                                        (255, 128, 0), -1)
                            
                            # Draw border around progress bar
                            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), 
                                        (255, 255, 255), 2)
                            
                            # Add text label with larger font
                            if progress_pct < 100:
                                label = f"CHECK: {progress_pct}%"
                                cv2.putText(frame, label, (bar_x + 5, bar_y + bar_height - 5), 
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                            else:
                                # When 100% ready, show different label
                                cv2.putText(frame, "CHECK READY", (bar_x + 5, bar_y + bar_height - 5), 
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                            
                            # Display current stability distance for debugging
                            stability_text = f"Stability: {track_data['current_distance']:.1f}/{STABILITY_THRESHOLD}"
                            cv2.putText(frame, stability_text, (bar_x, bar_y - 10),
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
                        
                        # If stable for required time and check not already triggered, trigger check
                        if stable_duration >= HOLD_DURATION and not track_data["check_triggered"]:
                            # Send check event
                            event_queue.put({
                                "source": "hand_tracking",
                                "event": "hand_detected",
                                "player_name": player_name,
                                "x": x,
                                "y": y
                            })
                            
                            # Mark check as triggered to prevent repeats
                            track_data["check_triggered"] = True
                            print(f"CHECK triggered for {player_name} after {stable_duration:.1f}s of stability")
                            
                            # Draw "CHECK" text on screen when triggered - MAKE IT MUCH LARGER
                            if frame is not None:
                                # Draw a attention-grabbing background
                                text_size = cv2.getTextSize("CHECK!", cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)[0]
                                text_x = int(x) - text_size[0] // 2
                                text_y = int(y) - 100
                                cv2.rectangle(frame, 
                                           (text_x - 10, text_y - text_size[1] - 10),
                                           (text_x + text_size[0] + 10, text_y + 10),
                                           (0, 0, 255), -1)
                                # Draw bold white text
                                cv2.putText(frame, "CHECK!", (text_x, text_y), 
                                          cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
                    else:
                        # Hand moved too much, reset stability
                        track_data["is_stable"] = False
                        # Only reset check_triggered when movement is very large (3x threshold)
                        if distance > STABILITY_THRESHOLD * 3:
                            track_data["check_triggered"] = False
                        # Update last position but use smoothed position to avoid jitter
                        track_data["last_position"] = (avg_x, avg_y)
            else:
                # Hand detected but not in any player area
                print(f"Hand detected outside player areas at coordinates ({x}, {y})")
        
        # Reset tracking data for areas where no hand is currently detected
        for player_name in PLAYER_AREAS.keys():
            if player_name not in detected_in_area:
                hand_tracking_data[player_name] = {
                    "last_position": None,
                    "start_time": 0,
                    "is_stable": False,
                    "check_triggered": False,
                    "recent_positions": [],
                    "current_distance": 0
                }
        
    def combined_sink(predictions: dict, video_frame: VideoFrame):
        # Create a copy of the image for our custom drawing
        frame = video_frame.image.copy() if video_frame.image is not None else None
        
        # Process hand detections and draw progress bars
        detected_in_area = set()
        current_time = time.time()
        
        for p in predictions.get('predictions', []):
            x, y = p['x'], p['y']
            player_name = get_player_from_coordinates(x, y)
            
            if player_name:
                detected_in_area.add(player_name)
                print(f"Hand detected in {player_name} area at coordinates ({x}, {y})")
                
                # Get tracking data for this player
                track_data = hand_tracking_data[player_name]
                last_pos = track_data["last_position"]
                
                # Update position and check stability
                if last_pos is None:
                    # First detection, initialize tracking
                    track_data["last_position"] = (x, y)
                    track_data["start_time"] = current_time
                    track_data["is_stable"] = True
                    track_data["check_triggered"] = False
                    track_data["recent_positions"] = [(x, y)]
                    track_data["current_distance"] = 0
                else:
                    # Add current position to recent positions list (for smoothing)
                    track_data["recent_positions"].append((x, y))
                    
                    # Keep only the most recent positions
                    if len(track_data["recent_positions"]) > POSITIONS_HISTORY:
                        track_data["recent_positions"] = track_data["recent_positions"][-POSITIONS_HISTORY:]
                    
                    # Get smoothed position (average of recent positions)
                    avg_x = sum(p[0] for p in track_data["recent_positions"]) / len(track_data["recent_positions"])
                    avg_y = sum(p[1] for p in track_data["recent_positions"]) / len(track_data["recent_positions"])
                    
                    # Calculate distance from last known position to smoothed position
                    distance = hand_distance((avg_x, avg_y), last_pos)
                    track_data["current_distance"] = distance
                    
                    if distance <= STABILITY_THRESHOLD:
                        # Hand is stable
                        if not track_data["is_stable"]:
                            # Hand just became stable, reset timer
                            track_data["start_time"] = current_time
                            track_data["is_stable"] = True
                        
                        # Check if hand has been stable for required duration
                        stable_duration = current_time - track_data["start_time"]
                        
                        # Calculate progress percentage (0-100%)
                        progress_pct = min(100, int((stable_duration / HOLD_DURATION) * 100))
                        
                        # Print feedback about stability progress
                        if progress_pct % 25 == 0 and not track_data["check_triggered"]:
                            print(f"{player_name} hand stable: {progress_pct}% towards CHECK")
                        
                        # Draw progress bar above hand position
                        if frame is not None and not track_data["check_triggered"]:
                            # Progress bar dimensions - MAKE IT LARGER AND MORE VISIBLE
                            bar_width = 150
                            bar_height = 25
                            bar_x = int(x) - bar_width // 2
                            bar_y = int(y) - 60  # Show bar above the hand
                            
                            # Draw progress bar background (gray)
                            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), 
                                        (100, 100, 100), -1)
                            
                            # Draw progress bar fill (bright blue) based on progress
                            fill_width = int((progress_pct / 100.0) * bar_width)
                            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill_width, bar_y + bar_height), 
                                        (255, 128, 0), -1)
                            
                            # Draw border around progress bar
                            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), 
                                        (255, 255, 255), 2)
                            
                            # Add text label with larger font
                            if progress_pct < 100:
                                label = f"CHECK: {progress_pct}%"
                                cv2.putText(frame, label, (bar_x + 5, bar_y + bar_height - 5), 
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                            else:
                                # When 100% ready, show different label
                                cv2.putText(frame, "CHECK READY", (bar_x + 5, bar_y + bar_height - 5), 
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                            
                            # Display current stability distance for debugging
                            stability_text = f"Stability: {track_data['current_distance']:.1f}/{STABILITY_THRESHOLD}"
                            cv2.putText(frame, stability_text, (bar_x, bar_y - 10),
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
                        
                        # If stable for required time and check not already triggered, trigger check
                        if stable_duration >= HOLD_DURATION and not track_data["check_triggered"]:
                            # Send check event
                            event_queue.put({
                                "source": "hand_tracking",
                                "event": "hand_detected",
                                "player_name": player_name,
                                "x": x,
                                "y": y
                            })
                            
                            # Mark check as triggered to prevent repeats
                            track_data["check_triggered"] = True
                            print(f"CHECK triggered for {player_name} after {stable_duration:.1f}s of stability")
                            
                            # Draw "CHECK" text on screen when triggered - MAKE IT MUCH LARGER
                            if frame is not None:
                                # Draw a attention-grabbing background
                                text_size = cv2.getTextSize("CHECK!", cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)[0]
                                text_x = int(x) - text_size[0] // 2
                                text_y = int(y) - 100
                                cv2.rectangle(frame, 
                                           (text_x - 10, text_y - text_size[1] - 10),
                                           (text_x + text_size[0] + 10, text_y + 10),
                                           (0, 0, 255), -1)
                                # Draw bold white text
                                cv2.putText(frame, "CHECK!", (text_x, text_y), 
                                          cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
                    else:
                        # Hand moved too much, reset stability
                        track_data["is_stable"] = False
                        # Only reset check_triggered when movement is very large (3x threshold)
                        if distance > STABILITY_THRESHOLD * 3:
                            track_data["check_triggered"] = False
                        # Update last position but use smoothed position to avoid jitter
                        track_data["last_position"] = (avg_x, avg_y)
            else:
                # Hand detected but not in any player area
                print(f"Hand detected outside player areas at coordinates ({x}, {y})")
        
        # Reset tracking data for areas where no hand is currently detected
        for player_name in PLAYER_AREAS.keys():
            if player_name not in detected_in_area:
                hand_tracking_data[player_name] = {
                    "last_position": None,
                    "start_time": 0,
                    "is_stable": False,
                    "check_triggered": False,
                    "recent_positions": [],
                    "current_distance": 0
                }
        
        # Render boxes on the video frame using the original method
        render_boxes(predictions, video_frame, annotator=None, display_size=(640,480))
        
        # Create a named window to display our frame with progress bars
        if frame is not None:
            cv2.imshow("Poker Hand Detection", frame)
            cv2.waitKey(1)

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
            # Don't re-import time here
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