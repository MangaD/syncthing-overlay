import requests
from datetime import datetime
import pytz

class SyncthingAPIClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.api_key = api_key

    def api_request(self, endpoint):
        headers = {"X-API-Key": self.api_key}
        try:
            response = requests.get(f"{self.base_url}{endpoint}", headers=headers, timeout=5)
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
