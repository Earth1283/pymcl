import os

APP_NAME = "PyMCLauncher"
MINECRAFT_DIR = os.path.join(os.path.expanduser("~"), ".pymcl-data")
IMAGES_DIR = os.path.join(MINECRAFT_DIR, "images")
DEFAULT_IMAGE_URL = "https://sm.ign.com/ign_ap/gallery/m/minecraft-/minecraft-vibrant-visuals-comparison-screenshots_25we.jpg"
DEFAULT_IMAGE_PATH = os.path.join(IMAGES_DIR, "default_background.jpg")
MODS_DIR = os.path.join(MINECRAFT_DIR, "mods")
VERSIONS_CACHE_PATH = os.path.join(MINECRAFT_DIR, "versions_cache.json")
