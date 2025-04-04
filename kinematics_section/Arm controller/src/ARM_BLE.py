import asyncio
import re
import tkinter as tk
from bleak import BleakClient
import threading

# BLE Configuration
ble_address = "68:5E:1C:26:EC:48"
characteristic_uuid = "FFE1"

# Global Variables
buffer = ""
raw_text_storage = []
loop = asyncio.new_event_loop()  # Separate event loop for BLE
ble_client = None  # Global client instance

# Start asyncio event loop in a separate thread
def start_asyncio_loop():
    """Runs the asyncio event loop in a separate thread."""
    asyncio.set_event_loop(loop)
    loop.run_forever()

threading.Thread(target=start_asyncio_loop, daemon=True).start()

async def connect_ble():
    """Connects to BLE device and maintains the connection."""
    global ble_client
    ble_client = BleakClient(ble_address)
    
    while True:
        try:
            print(f"Connecting to {ble_address}...")
            await ble_client.connect()
            if ble_client.is_connected:
                print(f"✅ Connected to {ble_address}")
                await enable_notifications()
                return
        except Exception as e:
            print(f"⚠️ Connection failed: {e}, retrying in 2s...")
            await asyncio.sleep(2)

async def enable_notifications():
    """Enables notifications to continuously receive BLE data."""
    if ble_client and ble_client.is_connected:
        await ble_client.start_notify(characteristic_uuid, notification_handler)
        print(f"📡 Subscribed to notifications on {characteristic_uuid}")

async def write_to_ble(value):
    """Writes a command to the BLE device without disconnecting."""
    if ble_client and ble_client.is_connected:
        new_data = bytearray(value.encode('utf-8'))
        await ble_client.write_gatt_char(characteristic_uuid, new_data, response=True)
        print(f"✉️ Sent: {value}")
    else:
        print("⚠️ BLE Disconnected. Reconnecting...")
        await connect_ble()

def send_ble_command(value):
    """Schedules a BLE write operation from the Tkinter thread."""
    asyncio.run_coroutine_threadsafe(write_to_ble(value), loop)

async def notification_handler(sender, data):
    """Handles incoming BLE notifications and processes the data."""
    global buffer
    chunk = data.decode('utf-8', errors='ignore')

    if chunk.startswith("DSD TECH:"):
        chunk = chunk.replace("DSD TECH:", "").strip()
    
    buffer += chunk

    while '{' in buffer and '}' in buffer:
        start = buffer.find('{')
        end = buffer.find('}')
        if start < end:
            complete_message = buffer[start:end + 1]
            raw_text_storage.append(complete_message)

            pattern = r"\{([\d.]+)s:([\d.]+),([\d.]+),([\d.]+),([\d.]+),([\d.]+),([\d.]+):([\d.]+),([\d.]+),([\d.]+),([\d.]+)\}"
            match = re.match(pattern, complete_message)

            if match:
                time, s0, s1, s2, s3, s4, s5, leftDuty, rightDuty, speedL, speedR = match.groups()
                positions = [-0.0, -3.0, -1.0, 1.0, 3.0, 0.0]

                ratio = sum(positions[i] * float(match.groups()[i + 1]) for i in range(6))
                ratio2 = (-float(leftDuty) + float(rightDuty))
                total = sum(float(match.groups()[i + 1]) for i in range(6))

                print(f"{complete_message} R:{round(ratio, 2)} ;D:{round(ratio2, 3)};S:{round(total, 2)}")
            else:
                print(f"{complete_message}")

            buffer = buffer[end + 1:]
        else:
            buffer = buffer[start:]
            
def stop_program():
    """Stops the BLE connection and exits the program safely."""
    global running
    running = False  # Stop reconnection attempts

    async def stop_ble():
        """Disconnects BLE and stops the asyncio loop."""
        global ble_client
        if ble_client and ble_client.is_connected:
            await ble_client.disconnect()
            print("🔴 BLE Disconnected.")

        loop.stop()  # Stop asyncio loop

    asyncio.run_coroutine_threadsafe(stop_ble(), loop)
    root.quit()  # Close Tkinter UI

####### FUNCTIONS ########
    
def set_pin(pin, status):
    stat_str = "on" if status else "off"
    full_str =  str(stat_str) + '=' + pin
    send_ble_command('{' + full_str + '}')

def suck():
    send_ble_command('{suck=0}')

def unsuck():
    send_ble_command('{suck=1}')

def set_angles(angles, relative_speeds):
    message = "{"
    for i in range(4):
        message+="angle"+str(i)+"="+angles[i]+";"
    for i in range(4):
        message+="speed"+str(i)+"="+relative_speeds[i]+";"
    send_ble_command(message + "}")

def req_status():
    send_ble_command("{req_status=1}")

########### GUI SETUP ##############

root = tk.Tk()
root.title("ARM BLE Interface")

# Set Pin
tk.Label(root, text="Pin Number").grid(row=0, column=0)
pin_entry = tk.Entry(root)
pin_entry.grid(row=0, column=1)

tk.Label(root, text="Status (0/1)").grid(row=0, column=2)
status_var = tk.IntVar()
status_check = tk.Checkbutton(root, variable=status_var)
status_check.grid(row=0, column=3)

def on_set_pin():
    try:
        pin = pin_entry.get()
        status = status_var.get()
        set_pin(pin, status)
    except Exception as e:
        messagebox.showerror("Error", str(e))

tk.Button(root, text="Set Pin", command=on_set_pin).grid(row=0, column=4, pady = 20)

# Suck / Unsuck
tk.Button(root, text="Suck", command=suck).grid(row=1, column=0)
tk.Button(root, text="Unsuck", command=unsuck).grid(row=1, column=1, pady = 20)

# Set Angles
angle_entries = []
speed_entries = []

# Set Angles
tk.Label(root, text="Angles (-135 to 135)").grid(row=2, column=0, columnspan=5)

tk.Label(root, text="Motor").grid(row=3, column=0)
for i in range(4):
    tk.Label(root, text=f"{i+1}").grid(row=3, column=i+1)
    e = tk.Entry(root, width=5)
    e.insert(0, "0")  # Default value
    e.grid(row=4, column=i+1)
    angle_entries.append(e)

# Set Relative Speeds
tk.Label(root, text="Rel Speeds (-135 to 135)").grid(row=5, column=0, columnspan=5)

tk.Label(root, text="Motor").grid(row=6, column=0)
for i in range(4):
    tk.Label(root, text=f"{i+1}").grid(row=6, column=i+1)
    e = tk.Entry(root, width=5)
    e.insert(0, "0")  # Default value
    e.grid(row=7, column=i+1)
    speed_entries.append(e)

def on_set_angles():
    try:
        angles = [e.get() for e in angle_entries]
        speeds = [e.get() for e in speed_entries]
        set_angles(angles, speeds)
    except Exception as e:
        messagebox.showerror("Error", str(e))

tk.Button(root, text="Set Angles", command=on_set_angles).grid(row=8, column=0, columnspan=4, pady = 20)

tk.Button(root, text="Request Status", command=req_status).grid(row=9, column=0, columnspan=4, pady = 20)

asyncio.run_coroutine_threadsafe(connect_ble(), loop)

# --- MAIN LOOP ---
root.mainloop()
