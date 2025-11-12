from pymcl.main import main
import os


def check_dirs() -> None:
    MINECRAFT_DIR = os.path.join(os.path.expanduser("~"), ".pymcl-data")
    IMAGES_DIR = os.path.join(MINECRAFT_DIR, "images")
    MODS_DIR = os.path.join(MINECRAFT_DIR, "mods") 
    if not os.path.exists(MINECRAFT_DIR):
        os.makedirs(MINECRAFT_DIR)
    os.makedirs(IMAGES_DIR, exist_ok=True)
    os.makedirs(MODS_DIR, exist_ok=True)

if __name__ == "__main__":
    check_dirs()
    main()
