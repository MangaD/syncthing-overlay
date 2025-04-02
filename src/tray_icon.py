from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw
import platform
import os

def create_tray_icon(toggle_overlay_callback, exit_callback, set_api_key_callback):
    """Create and return a system tray icon."""
    # Generate or load an icon
    if platform.system() == "Windows":
        icon_path = os.path.expandvars(r"%LOCALAPPDATA%\Programs\Syncthing\syncthing.ico")
    elif platform.system() == "Linux":
        icon_path = "/usr/share/icons/hicolor/512x512/apps/syncthing.png"
    else:
        icon_path = None

    if icon_path and os.path.exists(icon_path):
        icon_image = Image.open(icon_path)
    else:
        icon_image = Image.new("RGB", (64, 64), (255, 255, 255))
        draw = ImageDraw.Draw(icon_image)
        draw.rectangle((16, 16, 48, 48), fill="black")

    # Define tray menu
    menu = Menu(
        MenuItem("Set API Key", set_api_key_callback),
        MenuItem("Toggle Overlay", toggle_overlay_callback),
        MenuItem("Exit", exit_callback)
    )

    # Create and return the tray icon
    return Icon("SyncthingOverlay", icon_image, "Syncthing Overlay", menu)
