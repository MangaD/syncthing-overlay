import tkinter as tk
import requests
import time
from threading import Thread
from datetime import datetime
import pytz
import configparser
from pystray import Icon, Menu, MenuItem  # Added for tray icon
from PIL import Image, ImageDraw  # Added for tray icon
import os
import platform

# Configuration
SYNCTHING_URL = "http://localhost:8384"
UPDATE_INTERVAL = 5

class SyncthingOverlay:
    def __init__(self):
        # Load config
        config = configparser.ConfigParser()
        config.read("config.ini")
        self.api_key = config.get("syncthing", "api_key", fallback="your-api-key-here")

        self.root = tk.Tk()
        self.root.title("Syncthing Status")
        self.root.attributes("-alpha", 0.7)
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)

        self.status_label = tk.Label(self.root, text="Fetching Syncthing status...", 
                                    font=("Arial", 10, "bold"), bg="black", fg="white", 
                                    justify="left", anchor="nw", padx=10, pady=10)
        self.status_label.pack(fill="both", expand=True)

        self.root.bind("<Button-1>", self.start_drag)
        self.root.bind("<B1-Motion>", self.drag)

        self.running = True
        self.update_thread = Thread(target=self.update_status)
        self.update_thread.daemon = True
        self.update_thread.start()

        # Create tray icon
        self.tray_icon = None
        self.create_tray_icon()

    def start_drag(self, event):
        self.x = event.x
        self.y = event.y

    def drag(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def api_request(self, endpoint):
        headers = {"X-API-Key": self.api_key}
        try:
            response = requests.get(f"{SYNCTHING_URL}{endpoint}", headers=headers, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}

    def get_folder_status(self):
        folders = self.api_request("/rest/config/folders")
        if "error" in folders:
            return {"error": folders["error"]}

        folder_status = {}
        for folder in folders:
            folder_id = folder["id"]
            label = folder["label"] or folder_id
            status = self.api_request(f"/rest/db/status?folder={folder_id}")
            
            if isinstance(status, dict) and "error" in status and status["error"]:
                folder_status[label] = {
                    "state": f"Error ({status['error']})",
                    "last_update": "N/A",
                    "size": 0
                }
            else:
                state = status.get("state", "Unknown")
                in_sync_files = status.get("inSyncFiles", 0)
                global_files = status.get("globalFiles", 0)
                need_files = status.get("needFiles", 0)
                errors = status.get("errors", 0)
                error_msg = status.get("error", "")
                state_changed = status.get("stateChanged", "N/A")
                in_sync_bytes = status.get("inSyncBytes", 0) / (1024**3)

                sync_status = f"{state.capitalize()}"
                if need_files > 0:
                    sync_status += f" ({need_files} files needed)"
                elif global_files > 0:
                    sync_status += f" ({in_sync_files}/{global_files} files)"

                if errors > 0 or error_msg:
                    sync_status += f" (Errors: {errors or error_msg})"

                folder_status[label] = {
                    "state": sync_status,
                    "last_update": state_changed.split("T")[1][:8] if "T" in state_changed else "N/A",
                    "size": round(in_sync_bytes, 2)
                }
        return folder_status

    def get_device_status(self):
        devices = self.api_request("/rest/config/devices")
        connections = self.api_request("/rest/system/connections")
        status = self.api_request("/rest/system/status")
        if "error" in devices or "error" in connections or "error" in status:
            return {"error": "API error"}

        device_status = {}
        my_id = status.get("myID")
        if not my_id:
            return {"error": "Could not determine local device ID"}

        current_time = datetime.now(pytz.timezone("Europe/London"))
        for device in devices:
            device_id = device["deviceID"]
            if device_id != my_id:
                conn = connections["connections"].get(device_id, {})
                name = device["name"] or device_id[:8]
                
                if conn.get("connected", False):
                    started_at = datetime.fromisoformat(conn["startedAt"].replace("Z", "+00:00"))
                    duration = current_time - started_at
                    hours, remainder = divmod(int(duration.total_seconds()), 3600)
                    minutes = remainder // 60
                    in_mb = conn["inBytesTotal"] / (1024**2)
                    out_mb = conn["outBytesTotal"] / (1024**2)
                    status = f"Connected ({hours}h {minutes}m, v{conn['clientVersion']}, In: {round(in_mb, 2)} MB, Out: {round(out_mb, 2)} MB)"
                else:
                    status = "Disconnected"
                
                device_status[name] = status
        return device_status

    def update_status(self):
        while self.running:
            folder_status = self.get_folder_status()
            device_status = self.get_device_status()

            status_text = "Syncthing Status\n\nFolders:\n"
            if "error" in folder_status:
                status_text += f"Error: {folder_status['error']}\n"
            else:
                for folder, info in folder_status.items():
                    status_text += f"{folder}: {info['state']} ({info['size']} GB) (Last: {info['last_update']})\n"

            status_text += "\nDevices:\n"
            if "error" in device_status:
                status_text += f"Error: {device_status['error']}\n"
            else:
                for device, state in device_status.items():
                    status_text += f"{device}: {state}\n"

            self.status_label.config(text=status_text)
            self.root.update_idletasks()
            width = self.status_label.winfo_reqwidth() + 20
            height = self.status_label.winfo_reqheight() + 0
            self.root.geometry(f"{width}x{height}")

            time.sleep(UPDATE_INTERVAL)

    def create_tray_icon(self):
        # Determine the icon path based on the operating system
        if platform.system() == "Windows":
            icon_path = os.path.expandvars(r"%LOCALAPPDATA%\Programs\Syncthing\syncthing.ico")
        elif platform.system() == "Linux":
            icon_path = "/usr/share/icons/hicolor/512x512/apps/syncthing.png"
        else:
            # Fallback to a generated icon if the platform is unsupported
            icon_image = Image.new("RGB", (64, 64), (255, 255, 255))
            draw = ImageDraw.Draw(icon_image)
            draw.rectangle((16, 16, 48, 48), fill="black")
            icon_path = None

        # Load the icon image
        if icon_path and os.path.exists(icon_path):
            icon_image = Image.open(icon_path)
        else:
            # Use the fallback icon if the file is not found
            icon_image = Image.new("RGB", (64, 64), (255, 255, 255))
            draw = ImageDraw.Draw(icon_image)
            draw.rectangle((16, 16, 48, 48), fill="black")

        # Define tray menu
        menu = Menu(
            MenuItem("Toggle Overlay", self.toggle_overlay),
            MenuItem("Exit", self.exit_application)
        )

        # Create the tray icon
        self.tray_icon = Icon("SyncthingOverlay", icon_image, "Syncthing Overlay", menu)

        # Start the tray icon in a separate thread
        Thread(target=self.tray_icon.run, daemon=True).start()

    def toggle_overlay(self):
        if self.root.state() == "withdrawn":
            self.root.deiconify()
        else:
            self.root.withdraw()

    def exit_application(self):
        self.running = False
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()
        self.root.destroy()  # Ensure the Tkinter main loop is terminated

    def run(self):
        self.root.withdraw()  # Start with the overlay hidden
        self.root.mainloop()

    def stop(self):
        self.running = False
        self.root.quit()

if __name__ == "__main__":
    overlay = SyncthingOverlay()
    try:
        overlay.run()
    except KeyboardInterrupt:
        overlay.stop()