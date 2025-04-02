import time
from threading import Thread
from config import load_api_key, save_api_key
from api_client import SyncthingAPIClient
from tray_icon import create_tray_icon
from overlay import OverlayWindow
from tkinter.simpledialog import askstring

SYNCTHING_URL = "http://localhost:8384"
UPDATE_INTERVAL = 5

class SyncthingOverlay:
    def __init__(self):
        self.api_key = load_api_key()
        if not self.api_key:
            self.prompt_for_api_key()

        self.api_client = SyncthingAPIClient(SYNCTHING_URL, self.api_key)
        self.overlay = OverlayWindow()

        self.running = True
        self.update_thread = Thread(target=self.update_status_loop)
        self.update_thread.daemon = True
        self.update_thread.start()

        self.tray_icon = create_tray_icon(self.overlay.toggle, self.exit_application, self.prompt_for_api_key)
        Thread(target=self.tray_icon.run, daemon=True).start()

    def prompt_for_api_key(self):
        new_api_key = askstring("Set API Key", "Enter your Syncthing API Key:")
        if new_api_key:
            self.api_key = new_api_key
            save_api_key(new_api_key)

    def update_status_loop(self):
         while self.running:
            folder_status = self.api_client.get_folder_status()
            device_status = self.api_client.get_device_status()

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

            self.overlay.status_label.config(text=status_text)
            self.overlay.root.update_idletasks()
            width = self.overlay.status_label.winfo_reqwidth() + 20
            height = self.overlay.status_label.winfo_reqheight() + 0
            self.overlay.root.geometry(f"{width}x{height}")

            time.sleep(UPDATE_INTERVAL)

    def exit_application(self):
        self.running = False
        if self.tray_icon:
            self.tray_icon.stop()
        self.overlay.root.quit()
        self.overlay.root.destroy()  # Ensure the Tkinter main loop is terminated

    def run(self):
        self.overlay.run()

if __name__ == "__main__":
    overlay = SyncthingOverlay()
    try:
        overlay.run()
    except KeyboardInterrupt:
        overlay.exit_application()