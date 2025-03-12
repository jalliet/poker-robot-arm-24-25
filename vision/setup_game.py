import tkinter as tk
import json
import os

CONFIG_FILE = "vision/config.json"

# Default chip values
DEFAULT_CHIP_VALUES = {"white": 1, "red": 5, "blue": 10, "black": 25}
DEFAULT_PLAYER_TOTAL = 3000

class PokerGameSetupUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Poker Game Setup")
        self.root.geometry("300x400")
        self.root.configure(bg="#f0f0f0")  # Light gray background

        # Load existing config
        self.config = self.load_config()
        self.players = [key for key in self.config.keys() if "player" in key]

        # Variables
        self.chip_values = {color: tk.IntVar(value=self.config.get("chip_values", DEFAULT_CHIP_VALUES).get(color, value))
                           for color, value in DEFAULT_CHIP_VALUES.items()}
        self.player_totals = {player: tk.IntVar(value=self.config.get("player_totals", {}).get(player, DEFAULT_PLAYER_TOTAL))
                             for player in self.players}

        # Build UI
        self.create_widgets()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        return {}

    def create_widgets(self):
        # Title
        tk.Label(self.root, text="Game Setup", font=("Arial", 14, "bold"), bg="#f0f0f0").pack(pady=10)

        # Chip Values Frame
        chip_frame = tk.Frame(self.root, bg="#f0f0f0")
        chip_frame.pack(pady=5)
        tk.Label(chip_frame, text="Chip Values", font=("Arial", 10, "bold"), bg="#f0f0f0").pack()

        for color, var in self.chip_values.items():
            row = tk.Frame(chip_frame, bg="#f0f0f0")
            row.pack(pady=2)
            tk.Label(row, text=f"{color.capitalize()}:", bg="#f0f0f0", width=10).pack(side=tk.LEFT)
            tk.Entry(row, textvariable=var, width=10).pack(side=tk.LEFT)

        # Player Totals Frame
        player_frame = tk.Frame(self.root, bg="#f0f0f0")
        player_frame.pack(pady=5)
        tk.Label(player_frame, text="Player Totals", font=("Arial", 10, "bold"), bg="#f0f0f0").pack()

        for player, var in self.player_totals.items():
            row = tk.Frame(player_frame, bg="#f0f0f0")
            row.pack(pady=2)
            tk.Label(row, text=f"{player}:", bg="#f0f0f0", width=10).pack(side=tk.LEFT)
            tk.Entry(row, textvariable=var, width=10).pack(side=tk.LEFT)

        # Save Button
        tk.Button(self.root, text="Save", command=self.save_config, bg="#4CAF50", fg="white", width=10).pack(pady=20)

    def save_config(self):
        updated_config = self.config.copy()
        updated_config["chip_values"] = {color: var.get() for color, var in self.chip_values.items()}
        updated_config["player_totals"] = {player: var.get() for player, var in self.player_totals.items()}

        with open(CONFIG_FILE, "w") as f:
            json.dump(updated_config, f, indent=4)

        tk.Label(self.root, text="Saved!", bg="#f0f0f0", fg="green").pack(pady=5)

def main():
    root = tk.Tk()
    PokerGameSetupUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()