import os

APP_NAME = "PyMCLauncher"
CLIENT_ID = "34851193-4344-4028-b5b8-9fc87315984c"
REDIRECT_URL = "http://localhost:8000"
MINECRAFT_DIR = os.path.join(os.path.expanduser("~"), ".pymcl-data")
IMAGES_DIR = os.path.join(MINECRAFT_DIR, "images")
DEFAULT_IMAGE_URL = "https://sm.ign.com/ign_ap/gallery/m/minecraft-/minecraft-vibrant-visuals-comparison-screenshots_25we.jpg"
DEFAULT_IMAGE_PATH = os.path.join(IMAGES_DIR, "default_background.jpg")
MODS_DIR = os.path.join(MINECRAFT_DIR, "mods")
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
