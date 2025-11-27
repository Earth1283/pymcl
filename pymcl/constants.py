import os
import json

APP_NAME = "PyMCLauncher"
CLIENT_ID = "34851193-4344-4028-b5b8-9fc87315984c"
REDIRECT_URL = "http://localhost:8000"

def load_settings():
    try:
        with open("pymcl/config/settings.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

settings = load_settings()
MINECRAFT_DIR = settings.get("minecraft_dir", os.path.join("D:\\pymcl-data" if os.name == "nt" else os.path.join(os.path.expanduser("~"), ".pymcl-data")))
IMAGES_DIR = settings.get("images_dir", os.path.join(MINECRAFT_DIR, "images"))
MODS_DIR = settings.get("mods_dir", os.path.join(MINECRAFT_DIR, "mods"))
ICON_CACHE_DIR = os.path.join(MODS_DIR, ".icons")

DEFAULT_IMAGE_URL = "https://sm.ign.com/ign_ap/gallery/m/minecraft-/minecraft-vibrant-visuals-comparison-screenshots_25we.jpg"
DEFAULT_IMAGE_PATH = os.path.join(IMAGES_DIR, "default_background.jpg")
VERSIONS_CACHE_PATH = os.path.join(MINECRAFT_DIR, "versions_cache.json")
MICROSOFT_INFO_PATH = os.path.join(MINECRAFT_DIR, "microsoft_info.json")

from typing import TypedDict

class MicrosoftInfo(TypedDict):
    access_token: str
    refresh_token: str
    username: str
    uuid: str
    expires_in: int
    login_time: int
