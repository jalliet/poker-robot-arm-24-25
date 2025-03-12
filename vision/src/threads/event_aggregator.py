import threading
import time
import queue
import cv2
import requests
import json
from ..game_state import GameState, PlayerAction

# AI Server configuration
AI_SERVER_URL = "http://localhost:5000/api/action"

def event_aggregator_thread(event_queue, stop_event, chip_detection_event=None):
    """
    Thread that aggregates events from various sources, updates game state,
    and sends actions to the AI server
    """
    print("Event Aggregator thread started")
    
    # Initialize game state with chip_detection_event
    game_state = GameState(num_players=4, chip_detection_event=chip_detection_event)
    
    # Create a window for the UI
    cv2.namedWindow("Poker Game State", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Poker Game State", 800, 600)
    
    # Initialize UI immediately
    game_state.update_ui()
    game_state.display_ui()
    
    # Track pot amount
    current_pot_amount = 0
    previous_bet = 0
    
    # Map event sources to event types
    event_type_mapping = {
        "hand_tracking": "hand_movement",
        "chip_detection": "chip_count",
        "fold_detection": "fold_detected"
    }
    
    # Map PlayerAction enum to AI server action strings
    action_mapping = {
        PlayerAction.CHECK: "check",
        PlayerAction.CALL: "call",
        PlayerAction.RAISE: "raise",
        PlayerAction.FOLD: "fold"
    }
    
    def send_to_ai_server(player, action, amount, pot_amount):
        """Send action to AI server"""
        payload = {
            "action": action_mapping[action],
            "player": player,
            "amount": amount,
            "potAmount": pot_amount
        }
        
        print(f"Sending to AI server: {payload}")
        
        try:
            response = requests.post(AI_SERVER_URL, json=payload)
            if response.status_code == 200:
                print(f"Successfully sent action to AI server: {response.json()}")
            else:
                print(f"Error sending action to AI server: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Exception when sending action to AI server: {e}")
    
    while not stop_event.is_set():
        try:
            # Non-blocking queue get with timeout
            event = event_queue.get(block=True, timeout=0.1)
            
            # Process the event
            print(f"Received event: {event}")
            
            # Convert event format if needed
            processed_event = {}
            
            # Extract source and map to event type
            if "source" in event:
                source = event.get("source")
                if source in event_type_mapping:
                    processed_event["type"] = event_type_mapping[source]
            
            # If event already has a type, use it
            if "type" not in processed_event and "type" in event:
                processed_event["type"] = event.get("type")
                
            # Extract player information
            if "player" in event:
                processed_event["player"] = event.get("player")
            elif "player_name" in event:
                processed_event["player_name"] = event.get("player_name")
                
            # Copy other relevant fields
            for key in ["pot_increase", "previous_bet", "area", "event", "pot_value"]:
                if key in event:
                    processed_event[key] = event.get(key)
            
            # Special handling for fold detection events
            if "event" in event and event.get("event") == "fold" and "player_name" in event:
                processed_event["type"] = "fold_detected"
                player_name = event.get("player_name")
                if player_name.startswith("player_"):
                    try:
                        processed_event["player"] = int(player_name.split("_")[1])
                    except ValueError:
                        pass
            
            # Skip informational events from chip detection
            if event.get("source") == "chip_detection" and event.get("event") == "info":
                print(f"Skipping info event: {event}")
                event_queue.task_done()
                continue
                
            # Update pot amount for chip detection events
            if event.get("source") == "chip_detection" and event.get("event") == "pot_increase":
                if "pot_value" in event:
                    current_pot_amount = event.get("pot_value")
            
            # Update game state based on processed event
            if processed_event and "type" in processed_event:
                print(f"Processing event: {processed_event}")
                result = game_state.process_event(processed_event)
                
                if result:
                    if "error" in result:
                        print(f"Error: {result['error']} - Expected Player {result['expected']}, got Player {result['detected']}")
                    else:
                        player = result["player"]
                        action = result["action"]
                        
                        # Determine amount based on action type
                        amount = 0
                        if action in [PlayerAction.CALL, PlayerAction.RAISE]:
                            # For call/raise, use the pot_value from the event
                            if processed_event.get("type") == "chip_count" and "pot_value" in event:
                                # Calculate the amount the player added
                                amount = event.get("pot_value") - current_pot_amount + previous_bet
                                # Update previous_bet for next action
                                previous_bet = amount
                        
                        # Send action to AI server
                        send_to_ai_server(player, action, amount, current_pot_amount)
                        
                        print(f"Player {player} performed action: {action.value}, Amount: {amount}, Pot: {current_pot_amount}")
            
            # Mark task as done
            event_queue.task_done()
            
        except queue.Empty:
            # No event available, just continue
            pass
        
        # Update and display UI
        game_state.display_ui()
        
        # Small sleep to prevent CPU hogging
        time.sleep(0.01)
    
    # Clean up
    cv2.destroyWindow("Poker Game State")
    print("Event Aggregator thread stopped")