import tkinter as tk
from tkinter import scrolledtext
import requests
import json
import os
from dotenv import load_dotenv

# Load the environment variables
load_dotenv()


# API URL
BASE_URL = os.getenv("AI_SERVER_URL")

def test_endpoint(endpoint, method="GET", data=None):
    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}/{endpoint}")
        elif method == "POST":
            response = requests.post(f"{BASE_URL}/{endpoint}", json=data)
        else:
            output_text.insert(tk.END, f"Unsupported method: {method}\n")
            return

        output_text.insert(tk.END, f"Endpoint: {endpoint}\n")
        output_text.insert(tk.END, f"Status Code: {response.status_code}\n")
        output_text.insert(tk.END, f"Response:\n{json.dumps(response.json(), indent=2)}\n\n")
        output_text.yview(tk.END)
    except Exception as e:
        output_text.insert(tk.END, f"Error testing {endpoint}: {str(e)}\n\n")
        output_text.yview(tk.END)

# Tkinter GUI
root = tk.Tk()
root.title("API Tester")

# Buttons for each endpoint
button_frame = tk.Frame(root)
button_frame.pack(pady=10)

# Start Move Tracking
start_button = tk.Button(button_frame, text="Start Move Tracking", command=lambda: test_endpoint("start_move_tracking", method="POST"))
start_button.grid(row=0, column=0, padx=10, pady=5)

# Stop Move Tracking
stop_button = tk.Button(button_frame, text="Stop Move Tracking", command=lambda: test_endpoint("stop_move_tracking", method="POST"))
stop_button.grid(row=0, column=1, padx=10, pady=5)

# Get Move History
history_button = tk.Button(button_frame, text="Get Move History", command=lambda: test_endpoint("get_move_history"))
history_button.grid(row=0, column=2, padx=10, pady=5)

# Run YOLO for Chips
chips_button = tk.Button(button_frame, text="Run YOLO (Chips)", command=lambda: test_endpoint("run_yolo", method="POST", data={"model": "chips"}))
chips_button.grid(row=1, column=0, padx=10, pady=5)

# Run YOLO for Cards
cards_button = tk.Button(button_frame, text="Run YOLO (Cards)", command=lambda: test_endpoint("run_yolo", method="POST", data={"model": "cards"}))
cards_button.grid(row=1, column=1, padx=10, pady=5)

# Output text area
output_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=80, height=20)
output_text.pack(pady=10)

# Run the Tkinter event loop
root.mainloop()
