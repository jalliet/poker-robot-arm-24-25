import time
import threading
from enum import Enum
import cv2
import numpy as np

class PlayerAction(Enum):
    CHECK = "check"
    CALL = "call"
    RAISE = "raise"
    FOLD = "fold"
    NONE = "none"  # Used for initialization

class GameState:
    def __init__(self, num_players=4, chip_detection_event=None):
        self.num_players = num_players
        self.active_players = list(range(1, num_players + 1))  # Players 1-4
        self.current_player_idx = 0  # Index in active_players list
        self.move_history = []
        self.round_active = True
        self.chip_detection_event = chip_detection_event
        
        # For UI display
        self.ui_lock = threading.Lock()
        self.ui_image = None
        
        # Button area for chip counting
        self.button_area = [600, 500, 180, 50]  # [x, y, width, height]
        self.button_clicked = False
    
    def get_current_player(self):
        if not self.round_active or not self.active_players:
            return None
        return self.active_players[self.current_player_idx]
    
    def record_action(self, action, detected_player=None, additional_info=None):
        """Record the current player's action in the move history"""
        current_player = self.get_current_player()
        if not current_player:
            return None
            
        # If detected_player is provided, verify it matches the expected current player
        if detected_player is not None and detected_player != current_player:
            print(f"ERROR: Unexpected player detected. Expected Player {current_player}, got Player {detected_player}")
            return {"error": "unexpected_player", "expected": current_player, "detected": detected_player}
        
        timestamp = time.time()
        move = {
            "player": current_player,
            "action": action,
            "timestamp": timestamp,
            "info": additional_info
        }
        self.move_history.append(move)
        
        # If player folded, remove them from active players
        if action == PlayerAction.FOLD:
            self.active_players.remove(current_player)
            # If only one player remains, the round is over
            if len(self.active_players) == 1:
                self.round_active = False
                print(f"Round ended. Player {self.active_players[0]} wins!")
        
        # Move to next player
        if self.round_active and self.active_players:
            self.current_player_idx = (self.current_player_idx + 1) % len(self.active_players)
        
        # Update UI
        self.update_ui()
        
        return move
    
    def update_ui(self):
        """Update the UI display with current game state"""
        with self.ui_lock:
            # Create a blank image for UI
            ui_image = np.zeros((600, 800, 3), dtype=np.uint8)
            
            # Add title
            cv2.putText(ui_image, "Poker Game State", (20, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            # Show active players
            cv2.putText(ui_image, f"Active Players: {self.active_players}", 
                        (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
            
            # Show current player
            current_player = self.get_current_player()
            if current_player:
                cv2.putText(ui_image, f"Current Player: {current_player}", 
                            (20, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            else:
                cv2.putText(ui_image, "Round Complete", 
                            (20, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Display move history (most recent 10 moves)
            cv2.putText(ui_image, "Move History:", (20, 150), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
            
            y_pos = 190
            for i, move in enumerate(self.move_history[-10:]):
                move_text = f"Player {move['player']}: {move['action'].value}"
                if move['info']:
                    move_text += f" ({move['info']})"
                cv2.putText(ui_image, move_text, (40, y_pos + i*30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
            
            # Show round status
            status = "ACTIVE" if self.round_active else "ENDED"
            color = (0, 255, 0) if self.round_active else (0, 0, 255)
            cv2.putText(ui_image, f"Round Status: {status}", 
                        (20, 500), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            
            # Draw chip counting button
            x, y, w, h = self.button_area
            button_color = (0, 120, 255)  # Orange color
            cv2.rectangle(ui_image, (x, y), (x + w, y + h), button_color, -1)  # Filled rectangle
            cv2.rectangle(ui_image, (x, y), (x + w, y + h), (255, 255, 255), 2)  # White border
            cv2.putText(ui_image, "Count Chips", (x + 20, y + 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            self.ui_image = ui_image
    
    def display_ui(self):
        """Display the UI window"""
        with self.ui_lock:
            if self.ui_image is not None:
                cv2.imshow("Poker Game State", self.ui_image)
                key = cv2.waitKey(1)
                
                # Check for mouse clicks on the window
                cv2.setMouseCallback("Poker Game State", self.handle_mouse_click)
    
    def handle_mouse_click(self, event, x, y, flags, param):
        """Handle mouse clicks on the UI"""
        if event == cv2.EVENT_LBUTTONDOWN:
            # Check if click is within button area
            button_x, button_y, button_w, button_h = self.button_area
            if (button_x <= x <= button_x + button_w) and (button_y <= y <= button_y + button_h):
                print("Count Chips button clicked!")
                if self.chip_detection_event:
                    self.chip_detection_event.set()
    
    def process_event(self, event):
        """Process an event from the vision system"""
        if not self.round_active:
            return None
            
        current_player = self.get_current_player()
        if current_player is None:
            return None
            
        # Process different event types
        event_type = event.get("type")
        event_subtype = event.get("event")  # Check the event subtype
        
        # Skip informational events from chip detection
        if event.get("source") == "chip_detection" and event_subtype == "info":
            print(f"Skipping info event: {event}")
            return None
        
        # For events that include player information, extract it
        detected_player = None
        if "player" in event:
            detected_player = event.get("player")
        elif "player_name" in event:
            # Extract player number from name (e.g., "player_1" -> 1)
            player_name = event.get("player_name")
            if player_name and player_name.startswith("player_"):
                try:
                    detected_player = int(player_name.split("_")[1])
                except ValueError:
                    pass
        
        if event_type == "hand_movement":
            # Hand movement in player area indicates a check
            return self.record_action(PlayerAction.CHECK, detected_player)
            
        elif event_type == "chip_count":
            # Only process pot_increase events from chip detection
            if event_subtype == "pot_increase":
                pot_increase = event.get("pot_value", 0)
                previous_bet = event.get("previous_bet", 0)
                
                if pot_increase > previous_bet:
                    return self.record_action(PlayerAction.RAISE, detected_player, f"Amount: {pot_increase}")
                else:
                    return self.record_action(PlayerAction.CALL, detected_player, f"Amount: {pot_increase}")
                
        elif event_type == "fold_detected":
            # Cards detected in player area indicates a fold
            return self.record_action(PlayerAction.FOLD, detected_player)
            
        return None