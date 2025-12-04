import os
import subprocess
import uuid
import json
from typing import cast
import datetime
import glob
import hashlib

import minecraft_launcher_lib
import minecraft_launcher_lib.fabric
import requests
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from .constants import (
    MINECRAFT_DIR,
    VERSIONS_CACHE_PATH,
    DEFAULT_IMAGE_URL,
    DEFAULT_IMAGE_PATH,
    MODS_DIR,
    ICON_CACHE_DIR,
)


class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return o.isoformat()
        return super().default(o)


class VersionFetcher(QObject):
    finished = pyqtSignal(list, bool, str)

    @pyqtSlot()
    def run(self):
        try:
            versions = minecraft_launcher_lib.utils.get_version_list()

            try:
                with open(VERSIONS_CACHE_PATH, "w") as f:
                    json.dump(versions, f, cls=DateTimeEncoder)
                print(f"Version list cached to {VERSIONS_CACHE_PATH}")
            except Exception as e:
                print(f"Failed to save version cache: {e}")

            release_versions = [v["id"] for v in versions if v["type"] == "release"]
            self.finished.emit(release_versions, True, "Versions loaded successfully.")
        except Exception as e:
            error_msg = f"Error fetching versions: {str(e)}"
            print(error_msg)
            self.finished.emit([], False, error_msg)


class ImageDownloader(QObject):
    finished = pyqtSignal(bool, str)

    @pyqtSlot()
    def run(self):
        try:
            print(f"Downloading default image from {DEFAULT_IMAGE_URL}...")
            response = requests.get(DEFAULT_IMAGE_URL)
            response.raise_for_status()

            with open(DEFAULT_IMAGE_PATH, "wb") as f:
                f.write(response.content)

            print(f"Image saved to {DEFAULT_IMAGE_PATH}")
            self.finished.emit(True, DEFAULT_IMAGE_PATH)
        except Exception as e:
            error_msg = f"Error downloading image: {str(e)}"
            print(error_msg)
            self.finished.emit(False, error_msg)


class ModDownloader(QObject):
    finished = pyqtSignal(bool, str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    @pyqtSlot()
    def run(self):
        try:
            print(f"Downloading mod from {self.url}...")
            response = requests.get(self.url)
            response.raise_for_status()

            filename = ""
            if "content-disposition" in response.headers:
                disp = response.headers["content-disposition"]
                filename = disp.split("filename=")[-1].strip("'")

            if not filename:
                filename = self.url.split("/")[-1]

            if not filename.endswith(".jar"):
                if "?" in filename:
                    filename = filename.split("?")[0]
                if not filename.endswith(".jar"):
                    filename = f"{filename.split('.')[0]}.jar"

            save_path = os.path.join(MODS_DIR, filename)

            with open(save_path, "wb") as f:
                f.write(response.content)

            print(f"Mod saved to {save_path}")
            self.finished.emit(True, f"Downloaded '{filename}'")
        except Exception as e:
            error_msg = f"Error downloading mod: {str(e)}"
            print(error_msg)
            self.finished.emit(False, error_msg)


class IconDownloader(QObject):
    finished = pyqtSignal(str, str)

    def __init__(self, url, mod_id):
        super().__init__()
        self.url = url
        self.mod_id = mod_id

    @pyqtSlot()
    def run(self):
        try:
            response = requests.get(self.url)
            response.raise_for_status()

            # Create a unique filename for the icon
            filename = f"{self.mod_id}.png"
            save_path = os.path.join(ICON_CACHE_DIR, filename)

            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            with open(save_path, "wb") as f:
                f.write(response.content)
            self.finished.emit(self.mod_id, save_path)
        except Exception as e:
            print(f"Error downloading icon: {e}")
            self.finished.emit(self.mod_id, "")


class ProjectFetcher(QObject):
    finished = pyqtSignal(dict)

    def __init__(self, modrinth_client, slug):
        super().__init__()
        self.modrinth_client = modrinth_client
        self.slug = slug

    @pyqtSlot()
    def run(self):
        project_data = self.modrinth_client.get_project(self.slug)
        self.finished.emit(project_data)


class Worker(QObject):
    progress = pyqtSignal(int, int)
    status = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, version, options, mod_loader_type):
        super().__init__()
        self.version = version
        self.options = options
        self.mod_loader_type = mod_loader_type

    @pyqtSlot()
    def run(self):
        try:
            def set_status(text: str) -> None:
                self.status.emit(text)

            def set_progress(value: int, maximum: int = 100) -> None:
                self.progress.emit(value, maximum)

            self.version_to_launch = self.version

            set_status(f"Installing Minecraft {self.version}...")
            minecraft_launcher_lib.install.install_minecraft_version(
                version=self.version,
                minecraft_directory=MINECRAFT_DIR,
                callback={"setStatus": set_status, "setProgress": set_progress},
            )

            if self.mod_loader_type != "Vanilla":
                set_status(f"Installing {self.mod_loader_type}...")
                try:
                    if self.mod_loader_type == "Fabric":
                        loader_version = minecraft_launcher_lib.fabric.get_latest_loader_version()
                        set_status(f"Found Fabric Loader {loader_version}")
                        minecraft_launcher_lib.fabric.install_fabric(
                            minecraft_version=self.version,
                            minecraft_directory=MINECRAFT_DIR,
                            loader_version=loader_version,
                            callback={"setStatus": set_status, "setProgress": set_progress},
                        )
                        self.version_to_launch = f"fabric-loader-{loader_version}-{self.version}"
                    elif self.mod_loader_type in ["Forge", "NeoForge", "Quilt"]:
                        raise Exception(f"{self.mod_loader_type} installation is not supported in this version of PyMCL due to library limitations. Please update your libraries or use Fabric.")

                except Exception as loader_e:
                    print(f"{self.mod_loader_type} install failed: {loader_e}")
                    self.status.emit(f"{self.mod_loader_type} install failed: {loader_e}")
                    self.finished.emit(False, f"{self.mod_loader_type} install failed: {loader_e}")
                    return

            set_progress(1, 1)

            set_status("Getting launch command...")

            # Clean up options, removing keys with None or empty values
            # so that minecraft-launcher-lib can use its defaults.
            cleaned_options = {k: v for k, v in self.options.items() if v}

            command = minecraft_launcher_lib.command.get_minecraft_command(
                version=self.version_to_launch,
                minecraft_directory=MINECRAFT_DIR,
                options=cleaned_options,
            )

            set_status("Launching game...")
            self.progress.emit(0, 0)
            process = subprocess.Popen(command)
            process.wait()

            set_status("Game closed.")
            self.finished.emit(True, "Game closed.")

        except Exception as e:
            error_msg = f"An error occurred: {str(e)}"
            print(error_msg)
            self.status.emit(error_msg)
            self.finished.emit(False, error_msg)


class ModSearchWorker(QObject):
    finished = pyqtSignal(list, int)

    def __init__(self, modrinth_client, query, game_versions, loader, limit, search_id):
        super().__init__()
        self.modrinth_client = modrinth_client
        self.query = query
        self.game_versions = game_versions
        self.loader = loader
        self.limit = limit
        self.search_id = search_id

    @pyqtSlot()
    def run(self):
        try:
            results = self.modrinth_client.search(
                self.query,
                game_versions=self.game_versions,
                loader=self.loader,
                limit=self.limit
            )
            self.finished.emit(results, self.search_id)
        except Exception as e:
            print(f"Search error: {e}")
            self.finished.emit([], self.search_id)

class UpdateCheckerWorker(QObject):
    finished = pyqtSignal(dict) # {file_path: new_version_obj}

    def __init__(self, modrinth_client):
        super().__init__()
        self.client = modrinth_client

    @pyqtSlot()
    def run(self):
        print("UpdateCheckerWorker: Starting update check.")
        jar_files = glob.glob(os.path.join(MODS_DIR, "*.jar"))
        hashes = {} # {sha1: file_path}
        
        print(f"UpdateCheckerWorker: Found {len(jar_files)} jar files.")
        for path in jar_files:
            try:
                sha1 = self._calculate_sha1(path)
                hashes[sha1] = path
                print(f"UpdateCheckerWorker: Hashed {os.path.basename(path)}: {sha1}")
            except Exception as e:
                print(f"UpdateCheckerWorker: Error hashing {path}: {e}")
        
        if not hashes:
            print("UpdateCheckerWorker: No mods to check for updates.")
            self.finished.emit({})
            return

        print(f"UpdateCheckerWorker: Sending {len(hashes)} hashes to Modrinth for update check.")
        # Modrinth API allows bulk check
        updates = self.client.get_updates(list(hashes.keys()))
        print(f"UpdateCheckerWorker: Received update response from Modrinth. Found {len(updates)} updates.")
        
        # Map back to file paths: {file_path: new_version_data}
        result = {}
        for h, version in updates.items():
             if h in hashes:
                 result[hashes[h]] = version
                 print(f"UpdateCheckerWorker: Update available for {os.path.basename(hashes[h])}")
        
        print(f"UpdateCheckerWorker: Update check finished. Total updates found: {len(result)}")
        self.finished.emit(result)

    def _calculate_sha1(self, file_path):
        sha1 = hashlib.sha1()
        with open(file_path, 'rb') as f:
            while True:
                data = f.read(65536)
                if not data:
                    break
                sha1.update(data)
        return sha1.hexdigest()
