import tkinter as tk
from tkinter import messagebox, simpledialog

# ---------------------------------------------------------
# Pseudo code for chip counting using camera 2.
# In your full system, this function would grab a frame from camera 2,
# run your chip counting model, and return the number of chips detected.
# For now we simulate this by returning 0 (no chips detected)
# or by prompting the user if needed.
# ---------------------------------------------------------
def count_chips():
    # Pseudo-code:
    # frame = capture_frame_from_camera2()
    # chip_count = run_chip_count_model(frame)
    # return chip_count
    #
    # For simulation, assume no chips detected (0) or uncomment below to ask:
    # chip_count = simpledialog.askinteger("Chip Count", "Enter detected chip count:", initialvalue=0)
    # return chip_count if chip_count is not None else 0
    return 0

# ---------------------------------------------------------
# Player class holds each player’s name, chip count, and move history.
# ---------------------------------------------------------
class Player:
    def __init__(self, name, chips):
        self.name = name
        self.chips = chips
        self.all_in = False
        self.folded = False
        self.move_history = []

    def __str__(self):
        return f"{self.name}: ${self.chips} " + ("(All-in)" if self.all_in else "") + (" (Folded)" if self.folded else "")

# ---------------------------------------------------------
# PokerRound tracks the state of a betting round:
# - The list of players
# - The current bet amount that later players must match
# - The overall pot
# - The move history
# - Which player’s turn it is
# ---------------------------------------------------------
class PokerRound:
    def __init__(self, players):
        self.players = players  # list of Player objects
        self.current_bet = 0
        self.pot = 0
        self.move_history = []  # List of dicts, each with move details
        self.current_player_index = 0

    def record_move(self, player, move, amount=0):
        self.move_history.append({
            "player": player.name,
            "move": move,
            "amount": amount
        })
        player.move_history.append({
            "move": move,
            "amount": amount
        })
        print(f"Recorded move: {player.name} -> {move} (amount: ${amount})")

    def next_player(self):
        # Advance to the next player who has not folded.
        # (Here we assume one move per player for simplicity.)
        start_index = self.current_player_index
        while True:
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
            # Break if we have looped through all players
            if self.current_player_index == start_index:
                break
            if not self.players[self.current_player_index].folded:
                break

    def active_players(self):
        return [p for p in self.players if not p.folded]

    def round_over(self):
        """
        The betting round is over when:
        - Only one active player remains (others folded).
        - All active players have either called the highest bet or gone all-in.
        - No one has raised after the last call.
        """
        active_players = [p for p in self.players if not p.folded]
        
        if len(active_players) == 1:
            return True  # Only one player remains, round is over

        # Find the highest bet amount in the current round
        highest_bet = max((move["amount"] for move in self.move_history if move["move"] in ["Call", "Raise"]), default=0)

        # Check if all active players have matched the highest bet or are all-in
        for player in active_players:
            if not player.all_in and player.chips > 0:
                # Ensure the player has made at least one move before checking it
                if len(player.move_history) == 0 or player.move_history[-1]["move"] not in ["Call", "Raise"] or player.move_history[-1]["amount"] < highest_bet:
                    return False  # Someone still needs to call or fold

        return True  # No further action required, betting round is over




# ---------------------------------------------------------
# PokerUI builds the Tkinter user interface.
# First, you set the number of players and each player’s chip count.
# Then, when you click "Start Round", the game frame appears.
# The current player (in order P1, P2, P3, P4) is shown along with buttons
# to simulate the four possible moves.
# ---------------------------------------------------------
class PokerUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Poker Tracking System")
        self.players = []
        self.round = None

        # Setup frame for initial configuration.
        self.setup_frame = tk.Frame(root)
        self.setup_frame.pack(padx=10, pady=10)

        tk.Label(self.setup_frame, text="Number of Players (max 4):").grid(row=0, column=0)
        self.num_players_var = tk.IntVar(value=2)
        self.num_players_entry = tk.Entry(self.setup_frame, textvariable=self.num_players_var)
        self.num_players_entry.grid(row=0, column=1)

        self.player_entries = []  # To hold chip count entries for each player

        self.generate_players_button = tk.Button(self.setup_frame, text="Set Players", command=self.set_players)
        self.generate_players_button.grid(row=1, column=0, columnspan=2, pady=5)

        self.start_round_button = tk.Button(self.setup_frame, text="Start Round", command=self.start_round, state=tk.DISABLED)
        self.start_round_button.grid(row=2, column=0, columnspan=2, pady=5)

        # Game frame: This is where moves are taken during a round.
        self.game_frame = tk.Frame(root)

        self.current_player_label = tk.Label(self.game_frame, text="Current Player:")
        self.current_player_label.pack()

        self.move_history_text = tk.Text(self.game_frame, width=50, height=10, state=tk.DISABLED)
        self.move_history_text.pack(pady=5)

        # Buttons for moves:
        self.button_frame = tk.Frame(self.game_frame)
        self.button_frame.pack()

        self.check_button = tk.Button(self.button_frame, text="Check (X)", command=self.check_move)
        self.check_button.grid(row=0, column=0, padx=5)

        self.call_button = tk.Button(self.button_frame, text="Call (C)", command=self.call_move)
        self.call_button.grid(row=0, column=1, padx=5)

        self.raise_button = tk.Button(self.button_frame, text="Raise (R)", command=self.raise_move)
        self.raise_button.grid(row=0, column=2, padx=5)

        self.fold_button = tk.Button(self.button_frame, text="Fold (F)", command=self.fold_move)
        self.fold_button.grid(row=0, column=3, padx=5)

        self.status_label = tk.Label(self.game_frame, text="")
        self.status_label.pack(pady=5)

    def set_players(self):
        num_players = self.num_players_var.get()
        if num_players < 1 or num_players > 4:
            messagebox.showerror("Error", "Number of players must be between 1 and 4.")
            return

        # Destroy existing player entry fields to prevent duplication issues
        for widget in self.setup_frame.winfo_children():
            if isinstance(widget, tk.Entry) or isinstance(widget, tk.Label):
                widget.destroy()

        self.player_entries = []  # Reset player entries list

        for i in range(num_players):
            tk.Label(self.setup_frame, text=f"Player {i+1} Chip Count ($):").grid(row=i+1, column=0)
            entry = tk.Entry(self.setup_frame)
            entry.grid(row=i+1, column=1)
            self.player_entries.append(entry)

        # Ensure the Start Round button is still present and properly updated
        self.start_round_button.grid(row=num_players + 1, column=0, columnspan=2, pady=5)
        self.start_round_button.config(state=tk.NORMAL)  # Enable button

    def start_round(self):
        # Read the chip counts from the entries and create Player objects.
        self.players = []
        for i, entry in enumerate(self.player_entries):
            try:
                chips = int(entry.get())
            except ValueError:
                messagebox.showerror("Error", f"Invalid chip count for Player {i+1}.")
                return
            self.players.append(Player(f"Player {i+1}", chips))
        self.round = PokerRound(self.players)
        self.setup_frame.pack_forget()  # Hide the setup frame
        self.game_frame.pack(padx=10, pady=10)
        self.update_current_player_label()
        self.update_move_history_text()

    # --- Update UI ---
    def update_current_player_label(self):
        if self.round:
            current_player = self.round.players[self.round.current_player_index]
            self.current_player_label.config(text=f"Current Player: {current_player.name} (${current_player.chips})")
        else:
            self.current_player_label.config(text="No current player.")

    def update_move_history_text(self):
        self.move_history_text.config(state=tk.NORMAL)
        self.move_history_text.delete("1.0", tk.END)
        for move in self.round.move_history:
            self.move_history_text.insert(tk.END, f"{move['player']} -> {move['move']} (Amount: ${move['amount']})\n")
        self.move_history_text.config(state=tk.DISABLED)

    def print_chip_status(self):
        print("\n--- Player Chip Status ---")
        for player in self.round.players:
            print(f"{player.name}: ${player.chips}" + (" (All-in)" if player.all_in else "") + (" (Folded)" if player.folded else ""))
        print("----------------------------\n")

    # --- Move Handlers ---
    def check_move(self):
        # Check move is only allowed when no chips are detected in the pot.
        detected_chips = count_chips()
        current_player = self.round.players[self.round.current_player_index]
        if detected_chips > 0:
            messagebox.showerror("Invalid Move", "Chips detected in the pot. Cannot perform a Check move.")
            return
        # Record the move and update UI.
        self.round.record_move(current_player, "Check")
        self.status_label.config(text=f"{current_player.name} checks.")
        self.after_move()

    def call_move(self):
        current_player = self.round.players[self.round.current_player_index]

        # Ensure there is a bet to call
        if self.round.current_bet == 0:
            messagebox.showerror("Invalid Move", "No active bet to call. You must check or raise.")
            return

        # The player must call exactly the current bet amount
        call_amount = self.round.current_bet

        if current_player.chips < call_amount:
            # If the player does not have enough chips, they go all-in
            call_amount = current_player.chips
            current_player.all_in = True

        current_player.chips -= call_amount
        self.round.pot += call_amount
        self.round.record_move(current_player, "Call", call_amount)

        self.status_label.config(text=f"{current_player.name} calls with ${call_amount}. Remaining chips: ${current_player.chips}")
        self.print_chip_status()
        self.after_move()


    def raise_move(self):
        current_player = self.round.players[self.round.current_player_index]

        # Get the current highest bet
        current_bet = self.round.current_bet

        while True:  # Loop until the user enters a valid raise amount
            new_bet = simpledialog.askinteger("Raise", f"{current_player.name}, enter raise amount (must be greater than ${current_bet}):", initialvalue=current_bet+10)

            if new_bet is None:
                return  # Cancelled input

            if new_bet <= current_bet:
                messagebox.showerror("Error", "Raise amount must be greater than the current bet.")
                continue  # Re-prompt the player

            if new_bet > current_player.chips:
                messagebox.showerror("Error", "You cannot raise more than your remaining chips.")
                continue  # Re-prompt the player

            break  # Valid raise entered

        # Deduct chips and update the pot
        current_player.chips -= new_bet
        self.round.pot += new_bet
        self.round.current_bet = new_bet  # Update the new highest bet
        current_player.all_in = current_player.chips == 0  # Check if all-in

        self.round.record_move(current_player, "Raise", new_bet)
        self.status_label.config(text=f"{current_player.name} raises to ${new_bet}. Remaining chips: ${current_player.chips}")
        self.print_chip_status()
        self.after_move()


    def fold_move(self):
        current_player = self.round.players[self.round.current_player_index]
        # Mark the player as folded.
        current_player.folded = True
        self.round.record_move(current_player, "Fold")
        self.status_label.config(text=f"{current_player.name} folds.")
        self.after_move()

    # --- After a Move ---
    def after_move(self):
        # If the round is over, display a summary and then end.
        if self.round.round_over():
            self.end_round()
            return
        # Otherwise, move to the next player and update the display.
        self.round.next_player()
        self.update_current_player_label()
        self.update_move_history_text()

    def end_round(self):
        summary = f"Round Over! Total Pot: ${self.round.pot}\nMove History:\n"
        for move in self.round.move_history:
            summary += f"{move['player']} -> {move['move']} (Amount: ${move['amount']})\n"
        messagebox.showinfo("Round Summary", summary)
        self.game_frame.pack_forget()
        # For this demo we simply exit. In a full application, you might reset for a new round.
        self.root.quit()

# ---------------------------------------------------------
# Main: Create the Tkinter window and run the UI.
# ---------------------------------------------------------
if __name__ == '__main__':
    root = tk.Tk()
    app = PokerUI(root)
    root.mainloop()

