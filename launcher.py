import sys
import os
import subprocess
import uuid
import glob
import requests
import shutil
import json 
from typing import cast
import minecraft_launcher_lib

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QProgressBar,
    QFrame, QGraphicsDropShadowEffect, QCheckBox, QDialog, QListWidget, 
    QMessageBox, QListWidgetItem
)
from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot, Qt, QTimer, QUrl 
from PyQt6.QtGui import QIcon, QFont, QColor, QDesktopServices

try:
    from rich.traceback import install
    install(show_locals=True)
except Exception:
    pass # the user does not have rich, not using pretty printed exceptions

# --- Constants ---
APP_NAME = "PyMCLauncher"
MINECRAFT_DIR = os.path.join(os.path.expanduser("~"), ".pymcl-data")
IMAGES_DIR = os.path.join(MINECRAFT_DIR, "images")
DEFAULT_IMAGE_URL = "https://sm.ign.com/ign_ap/gallery/m/minecraft-/minecraft-vibrant-visuals-comparison-screenshots_25we.jpg"
DEFAULT_IMAGE_PATH = os.path.join(IMAGES_DIR, "default_background.jpg")
MODS_DIR = os.path.join(MINECRAFT_DIR, "mods") 
VERSIONS_CACHE_PATH = os.path.join(MINECRAFT_DIR, "versions_cache.json") 

if not os.path.exists(MINECRAFT_DIR):
    os.makedirs(MINECRAFT_DIR)
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(MODS_DIR, exist_ok=True) 


# --- Enhanced Dark Theme Stylesheet ---
STYLESHEET = """
QWidget {
    background-color: #1a1a1a;
    color: #f0f0f0;
    font-family: 'Segoe UI', Inter, sans-serif;
    font-size: 13px;
}
QMainWindow {
    background-color: #1a1a1a;
}
QFrame#central_widget_frame {
    border: none;
    border-radius: 16px;
    background-color: rgba(37, 37, 37, 0.85);
    padding: 10px;
}
QLabel {
    color: #e0e0e0;
    font-size: 13px;
    background: transparent;
}
QLabel#title_label {
    font-size: 36px;
    font-weight: 700;
    color: #ffffff;
    padding: 0px;
    background: transparent;
    letter-spacing: 1px;
}
QLabel#subtitle_label {
    font-size: 15px;
    color: #888;
    background: transparent;
    margin-top: 5px;
}
QLabel#section_label {
    font-size: 11px;
    font-weight: 600;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    background: transparent;
}
QLineEdit {
    background-color: #1e1e1e;
    border: 2px solid #3a3a3a;
    border-radius: 8px;
    padding: 0 18px;
    font-size: 15px;
    color: #ffffff;
    min-height: 55px;
}
QLineEdit:focus {
    border: 2px solid #4a9eff;
    background-color: #242424;
}
QLineEdit:hover {
    border: 2px solid #505050;
}
QComboBox {
    background-color: #1e1e1e;
    border: 2px solid #3a3a3a;
    border-radius: 8px;
    padding: 0 18px;
    font-size: 15px;
    color: #ffffff;
    min-height: 55px;
}
QComboBox:focus {
    border: 2px solid #4a9eff;
    background-color: #242424;
}
QComboBox:hover {
    border: 2px solid #505050;
}
QComboBox::drop-down {
    border: none;
    width: 30px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #888;
    margin-right: 8px;
}
QComboBox QAbstractItemView {
    background-color: #2d2d2d;
    border: 2px solid #3a3a3a;
    border-radius: 8px;
    selection-background-color: #4a9eff;
    selection-color: #ffffff;
    padding: 5px;
    outline: none;
}
QComboBox QAbstractItemView::item {
    padding: 8px 15px;
    border-radius: 4px;
}
QComboBox QAbstractItemView::item:hover {
    background-color: #3a3a3a;
}
QPushButton {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                      stop:0 #5ab0ff, stop:1 #4a9eff);
    color: #ffffff;
    border: none;
    border-radius: 10px;
    padding: 0 20px;
    font-size: 17px;
    font-weight: 600;
    letter-spacing: 1px;
    min-height: 55px;
}
QPushButton:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                      stop:0 #6ac0ff, stop:1 #5ab0ff);
}
QPushButton:pressed {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                      stop:0 #4a9eff, stop:1 #3a8eef);
}
QPushButton:disabled {
    background-color: #2a2a2a;
    color: #666;
}

QPushButton#secondary_button {
    background-color: #3a3a3a;
    color: #f0f0f0;
    border: 2px solid #505050;
    padding: 0 20px;
    font-size: 15px;
    font-weight: 600;
    min-height: 45px;
    border-radius: 8px;
}
QPushButton#secondary_button:hover {
    background-color: #4a4a4a;
    border-color: #606060;
}
QPushButton#secondary_button:pressed {
    background-color: #303030;
}
QPushButton#danger_button {
    background-color: #3a3a3a;
    color: #ff8080;
    border: 2px solid #505050;
    padding: 0 20px;
    font-size: 15px;
    font-weight: 600;
    min-height: 45px;
    border-radius: 8px;
}
QPushButton#danger_button:hover {
    background-color: #4a4a4a;
    border-color: #ff8080;
}
QPushButton#danger_button:pressed {
    background-color: #303030;
}
QProgressBar {
    border: none;
    border-radius: 8px;
    text-align: center;
    background-color: #1e1e1e;
    color: #ffffff;
    font-weight: 600;
    font-size: 13px;
    min-height: 32px;
}
QProgressBar::chunk {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                      stop:0 #4a9eff, stop:1 #5ab0ff);
    border-radius: 8px;
}
QLabel#status_label {
    color: #999;
    font-size: 13px;
    background: transparent;
    padding: 8px;
}

QCheckBox {
    spacing: 10px;
    font-size: 15px;
    font-weight: 600;
    color: #f0f0f0;
    background: transparent;
}
QCheckBox::indicator {
    width: 44px;
    height: 24px;
    border: 2px solid #505050;
    border-radius: 12px;
    background-color: #1e1e1e;
}
QCheckBox::indicator:hover {
    border-color: #606060;
}
QCheckBox::indicator:checked {
    background-color: #4a9eff;
    border-color: #4a9eff;
}
QCheckBox::indicator::handle {
    width: 18px;
    height: 18px;
    background-color: #f0f0f0;
    border-radius: 9px;
    margin: 3px;
}
QCheckBox::indicator:checked::handle {
    background-color: #ffffff;
    margin-left: 23px;
}

QListWidget {
    background-color: #1e1e1e;
    border: 2px solid #3a3a3a;
    border-radius: 8px;
    padding: 5px;
    font-size: 14px;
}
QListWidget::item {
    padding: 8px 12px;
    border-radius: 4px;
    color: #f0f0f0;
}
QListWidget::item:hover {
    background-color: #2a2a2a;
}
QListWidget::item:selected {
    background-color: #4a9eff;
    color: #ffffff;
}

QWidget#main_central_widget {
    background: transparent;
}

QWidget#left_title_container {
    background: transparent;
}

QFrame#title_frame {
    background-color: rgba(26, 26, 26, 0.75); /* Translucent background */
    border-radius: 12px;
}

QDialog {
    background-color: #252525;
}
"""
# qss done lol

# --- Worker Thread for Version Fetching ---
class VersionFetcher(QObject):
    finished = pyqtSignal(list, bool, str)

    @pyqtSlot()
    def run(self):
        try:
            versions = minecraft_launcher_lib.utils.get_version_list()
            
            # --- CACHE THE VERSIONS ---
            try:
                with open(VERSIONS_CACHE_PATH, 'w') as f:
                    json.dump(versions, f)
                print(f"Version list cached to {VERSIONS_CACHE_PATH}")
            except Exception as e:
                print(f"Failed to save version cache: {e}")
            # --- END CACHE ---

            release_versions = [v['id'] for v in versions if v['type'] == 'release']
            self.finished.emit(release_versions, True, "Versions loaded successfully.")
        except Exception as e:
            error_msg = f"Error fetching versions: {str(e)}"
            print(error_msg)
            self.finished.emit([], False, error_msg)


# --- Worker Thread for Image Downloading ---
class ImageDownloader(QObject):
    finished = pyqtSignal(bool, str)

    @pyqtSlot()
    def run(self):
        try:
            print(f"Downloading default image from {DEFAULT_IMAGE_URL}...")
            response = requests.get(DEFAULT_IMAGE_URL)
            response.raise_for_status()  # Raise an exception for bad status codes
            
            with open(DEFAULT_IMAGE_PATH, 'wb') as f:
                f.write(response.content)
                
            print(f"Image saved to {DEFAULT_IMAGE_PATH}")
            self.finished.emit(True, DEFAULT_IMAGE_PATH)
        except Exception as e:
            error_msg = f"Error downloading image: {str(e)}"
            print(error_msg)
            self.finished.emit(False, error_msg)


# --- Worker Thread for Mod Downloading ---
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
            
            # Try to get filename from headers
            filename = ""
            if "content-disposition" in response.headers:
                disp = response.headers['content-disposition']
                filename = disp.split("filename=")[-1].strip("\"'")
            
            # If not in headers, get from URL
            if not filename:
                filename = self.url.split("/")[-1]

            # Ensure it's a jar file
            if not filename.endswith(".jar"):
                if "?" in filename:
                    filename = filename.split("?")[0]
                if not filename.endswith(".jar"):
                     filename = f"{filename.split('.')[0]}.jar" # Best guess
            
            save_path = os.path.join(MODS_DIR, filename)
            
            with open(save_path, 'wb') as f:
                f.write(response.content)
                
            print(f"Mod saved to {save_path}")
            self.finished.emit(True, f"Downloaded '{filename}'")
        except Exception as e:
            error_msg = f"Error downloading mod: {str(e)}"
            print(error_msg)
            self.finished.emit(False, error_msg)


# --- Worker Thread for Blocking Tasks ---
class Worker(QObject):
    progress = pyqtSignal(int, int)
    status = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, version, username, use_fabric):
        super().__init__()
        self.version = version
        self.username = username
        self.use_fabric = use_fabric

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
                callback={"setStatus": set_status, "setProgress": set_progress}
            )

            if self.use_fabric:
                set_status("Installing Fabric...")
                try:
                    # Get latest loader version
                    loader_version = minecraft_launcher_lib.fabric.get_latest_loader_version()
                    set_status(f"Found Fabric Loader {loader_version}")
                    
                    # Install Fabric
                    minecraft_launcher_lib.fabric.install_fabric(
                        minecraft_version=self.version,  # <-- Changed from version= to minecraft_version=
                        minecraft_directory=MINECRAFT_DIR,
                        loader_version=loader_version,
                        callback={"setStatus": set_status, "setProgress": set_progress}
                    )
                    # The version ID for launching Fabric
                    self.version_to_launch = f"fabric-loader-{loader_version}-{self.version}"
                except Exception as fabric_e:
                    print(f"Fabric install failed: {fabric_e}")
                    self.status.emit(f"Fabric install failed: {fabric_e}")
                    self.finished.emit(False, f"Fabric install failed: {fabric_e}")
                    return

            set_progress(1, 1)
            
            options = cast(minecraft_launcher_lib.command.MinecraftOptions, {
                "username": self.username,
                "uuid": str(uuid.uuid4()),
                "token": ""
            })

            set_status("Getting launch command...")
            command = minecraft_launcher_lib.command.get_minecraft_command(
                version=self.version_to_launch, # <--- Use the correct version (vanilla or fabric)
                minecraft_directory=MINECRAFT_DIR,
                options=options
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


# --- Drag-and-Drop Mod List Widget ---
class ModListWidget(QListWidget):
    mods_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.DragDropMode.DropOnly)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            # Check if any file is a .jar file
            for url in event.mimeData().urls():
                if url.isLocalFile() and url.toLocalFile().endswith('.jar'):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        copied_count = 0
        for url in event.mimeData().urls():
            if url.isLocalFile():
                file_path = url.toLocalFile()
                if file_path.endswith('.jar'):
                    try:
                        filename = os.path.basename(file_path)
                        dest_path = os.path.join(MODS_DIR, filename)
                        shutil.copy(file_path, dest_path)
                        print(f"Copied mod {filename} to {MODS_DIR}")
                        copied_count += 1
                    except Exception as e:
                        print(f"Error copying mod {file_path}: {e}")
        
        if copied_count > 0:
            self.mods_changed.emit()

# --- Mod Manager Dialog ---
class ModManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mod Manager")
        self.setMinimumSize(600, 400)
        
        self.downloader_thread = None
        self.downloader = None

        self.init_ui()
        self.populate_mods_list()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Drop Label
        drop_label = QLabel("Drag & Drop .jar files here to install")
        drop_label.setObjectName("section_label")
        drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(drop_label)

        # Mod List
        self.mod_list_widget = ModListWidget()
        self.mod_list_widget.mods_changed.connect(self.populate_mods_list)
        layout.addWidget(self.mod_list_widget, 1) # Add stretch factor

        # Download from URL section
        download_label = QLabel("DOWNLOAD MOD FROM URL")
        download_label.setObjectName("section_label")
        layout.addWidget(download_label)

        download_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste mod .jar URL here...")
        download_layout.addWidget(self.url_input)

        self.download_button = QPushButton("Download")
        self.download_button.setObjectName("secondary_button")
        self.download_button.clicked.connect(self.start_mod_download)
        download_layout.addWidget(self.download_button)
        layout.addLayout(download_layout)

        # Status label
        self.download_status_label = QLabel("")
        self.download_status_label.setObjectName("status_label")
        layout.addWidget(self.download_status_label)

        # Button row
        button_layout = QHBoxLayout()
        
        open_folder_button = QPushButton("Open Mods Folder")
        open_folder_button.setObjectName("secondary_button")
        open_folder_button.clicked.connect(self.open_mods_folder)
        button_layout.addWidget(open_folder_button)
        
        delete_button = QPushButton("Delete Selected Mod")
        delete_button.setObjectName("danger_button")
        delete_button.clicked.connect(self.delete_selected_mod)
        button_layout.addWidget(delete_button)

        button_layout.addStretch(1)

        refresh_button = QPushButton("Refresh List")
        refresh_button.setObjectName("secondary_button")
        refresh_button.clicked.connect(self.populate_mods_list)
        button_layout.addWidget(refresh_button)

        layout.addLayout(button_layout)

    @pyqtSlot()
    def populate_mods_list(self):
        self.mod_list_widget.clear()
        try:
            jar_files = glob.glob(os.path.join(MODS_DIR, "*.jar"))
            for mod_path in jar_files:
                filename = os.path.basename(mod_path)
                item = QListWidgetItem(filename)
                item.setData(Qt.ItemDataRole.UserRole, mod_path) # Store full path
                self.mod_list_widget.addItem(item)
        except Exception as e:
            print(f"Error populating mods list: {e}")

    @pyqtSlot()
    def open_mods_folder(self):
        try:
            QDesktopServices.openUrl(QUrl.fromLocalFile(MODS_DIR))
        except Exception as e:
            print(f"Error opening mods folder: {e}")

    @pyqtSlot()
    def delete_selected_mod(self):
        selected_items = self.mod_list_widget.selectedItems()
        if not selected_items:
            return

        item = selected_items[0]
        mod_path = item.data(Qt.ItemDataRole.UserRole)
        filename = os.path.basename(mod_path)

        reply = QMessageBox.question(self, "Delete Mod", 
                                     f"Are you sure you want to delete '{filename}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                os.remove(mod_path)
                self.populate_mods_list()
            except Exception as e:
                print(f"Error deleting mod: {e}")
                QMessageBox.critical(self, "Error", f"Could not delete mod: {e}")

    @pyqtSlot()
    def start_mod_download(self):
        url = self.url_input.text().strip()
        if not url:
            return

        if not (url.startswith("http://") or url.startswith("https://")):
            url = "https://" + url
        
        self.download_button.setEnabled(False)
        self.download_button.setText("Downloading...")
        self.download_status_label.setText(f"Starting download from {url}...")

        self.downloader_thread = QThread()
        self.downloader = ModDownloader(url)
        self.downloader.moveToThread(self.downloader_thread)

        self.downloader_thread.started.connect(self.downloader.run)
        self.downloader.finished.connect(self.on_mod_download_finished)
        
        self.downloader.finished.connect(self.downloader_thread.quit)
        self.downloader.finished.connect(self.downloader.deleteLater)
        self.downloader_thread.finished.connect(self.downloader_thread.deleteLater)

        self.downloader_thread.start()

    @pyqtSlot(bool, str)
    def on_mod_download_finished(self, success, message):
        self.download_button.setEnabled(True)
        self.download_button.setText("Download")
        self.download_status_label.setText(message)
        
        if success:
            self.url_input.clear()
            self.populate_mods_list()


# --- Main GUI Window ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.worker_thread = None
        self.worker = None
        self.version_fetch_thread = None
        self.version_fetcher = None
        self.image_downloader_thread = None
        self.image_downloader = None
        self.bg_timer = None
        
        self.image_files = []
        self.current_image_index = 0

        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(900, 500)
        self.resize(900, 500)

        self.init_ui()
        self.apply_styles()
        self.add_shadow_effects()
        self.populate_versions()
        self.init_background_images()

    def init_ui(self):
        # Central widget and layout
        central_widget = QWidget()
        central_widget.setObjectName("main_central_widget")
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(40)

        # Left side - Title Section
        left_widget = QWidget()
        left_widget.setObjectName("left_title_container") # <--- GAVE IT AN OBJECT NAME
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(5)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # --- Wrap labels in a frame ---
        title_frame = QFrame()
        title_frame.setObjectName("title_frame") # <--- GAVE IT AN OBJECT NAME
        title_frame_layout = QVBoxLayout(title_frame)
        title_frame_layout.setSpacing(0) # <--- No spacing between title and subtitle
        title_frame_layout.setContentsMargins(20, 20, 20, 20) # <--- Padding inside the box

        title_label = QLabel(APP_NAME)
        title_label.setObjectName("title_label")
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        title_frame_layout.addWidget(title_label)
        
        subtitle_label = QLabel("Offline Minecraft Launcher")
        subtitle_label.setObjectName("subtitle_label")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        title_frame_layout.addWidget(subtitle_label)

        left_layout.addWidget(title_frame) # <--- Add the frame to the left layout
        # --- End of frame wrap ---
        
        left_layout.addStretch(1)
        
        main_layout.addWidget(left_widget, 2)
        
        # Right side - Frame for content
        content_frame = QFrame()
        content_frame.setObjectName("central_widget_frame")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(40, 40, 40, 40)
        content_layout.setSpacing(0) # <--- SLOP FIX: Set spacing to 0
        main_layout.addWidget(content_frame, 3)

        # Username Section
        username_label = QLabel("USERNAME")
        username_label.setObjectName("section_label")
        content_layout.addWidget(username_label)
        
        content_layout.addSpacing(5) # <--- SLOP FIX: Manual spacing

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.setText(f"Player{uuid.uuid4().hex[:6]}")
        self.username_input.setMinimumHeight(55) 
        content_layout.addWidget(self.username_input)

        content_layout.addSpacing(20) # <--- SLOP FIX: Manual spacing

        # Version Section
        version_label = QLabel("MINECRAFT VERSION")
        version_label.setObjectName("section_label")
        content_layout.addWidget(version_label)
        
        content_layout.addSpacing(5) # <--- SLOP FIX: Manual spacing

        self.version_combo = QComboBox()
        self.version_combo.setPlaceholderText("Loading versions...")
        self.version_combo.setMinimumHeight(55) 
        content_layout.addWidget(self.version_combo)

        content_layout.addSpacing(20) # <--- SLOP FIX: Manual spacing

        # --- Modding Section ---
        mod_layout = QHBoxLayout()
        mod_layout.setSpacing(15)

        self.fabric_toggle = QCheckBox("Use Fabric")
        mod_layout.addWidget(self.fabric_toggle, 0, Qt.AlignmentFlag.AlignVCenter) # <--- SLOP FIX: Added V-Center Alignment

        mod_layout.addStretch(1)

        self.mod_manager_button = QPushButton("Manage Mods")
        self.mod_manager_button.setObjectName("secondary_button")
        self.mod_manager_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mod_manager_button.clicked.connect(self.open_mod_manager)
        mod_layout.addWidget(self.mod_manager_button)
        
        content_layout.addLayout(mod_layout)
        # --- End Modding Section ---

        content_layout.addSpacing(20) # <--- SLOP FIX: Manual spacing

        # Launch Button
        self.launch_button = QPushButton("🚀 LAUNCH GAME")
        self.launch_button.clicked.connect(self.start_launch)
        self.launch_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.launch_button.setMinimumHeight(55) 
        content_layout.addWidget(self.launch_button)

        content_layout.addSpacing(15) # <--- SLOP FIX: Manual spacing

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setMinimumHeight(32) 
        content_layout.addWidget(self.progress_bar)

        content_layout.addSpacing(5) # <--- SLOP FIX: Manual spacing

        # Status Label
        self.status_label = QLabel("Ready to launch")
        self.status_label.setObjectName("status_label")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(self.status_label)
 
        # Add stretch at the very end
        content_layout.addStretch(1) 
    
    def apply_styles(self):
        self.setStyleSheet(STYLESHEET)
        
    def add_shadow_effects(self):
        """Add subtle shadow effects to key elements"""
        # Shadow for main content frame
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 5)
        self.findChild(QFrame, "central_widget_frame").setGraphicsEffect(shadow)

        # Shadow for title frame
        title_shadow = QGraphicsDropShadowEffect()
        title_shadow.setBlurRadius(20)
        title_shadow.setColor(QColor(0, 0, 0, 80))
        title_shadow.setOffset(0, 3)
        self.findChild(QFrame, "title_frame").setGraphicsEffect(title_shadow)
        
    def init_background_images(self):
        """Looks for background images and starts download or cycling."""
        print("Initializing background images...")
        self.image_files = glob.glob(os.path.join(IMAGES_DIR, "*.png")) + \
                           glob.glob(os.path.join(IMAGES_DIR, "*.jpg"))
        
        if not self.image_files:
            print("No images found. Downloading default image.")
            # Start downloader thread
            self.image_downloader_thread = QThread()
            self.image_downloader = ImageDownloader()
            self.image_downloader.moveToThread(self.image_downloader_thread)

            self.image_downloader_thread.started.connect(self.image_downloader.run)
            self.image_downloader.finished.connect(self.on_image_downloaded)
            
            self.image_downloader.finished.connect(self.image_downloader_thread.quit)
            self.image_downloader.finished.connect(self.image_downloader.deleteLater)
            self.image_downloader_thread.finished.connect(self.image_downloader_thread.deleteLater)

            self.image_downloader_thread.start()
        else:
            print(f"Found {len(self.image_files)} images.")
            self.update_background_image() # Set first image
            
            if len(self.image_files) > 1:
                print("Starting background image timer...")
                self.bg_timer = QTimer(self)
                self.bg_timer.timeout.connect(self.update_background_image)
                self.bg_timer.start(30000) # 30 seconds

    @pyqtSlot(bool, str)
    def on_image_downloaded(self, success, path):
        if success:
            self.image_files = [path]
            self.current_image_index = 0
            self.update_background_image()
        else:
            print(f"Failed to download background image: {path}")

    @pyqtSlot()
    def update_background_image(self):
        if not self.image_files:
            return
            
        path = self.image_files[self.current_image_index]
        self.current_image_index = (self.current_image_index + 1) % len(self.image_files)
        
        # Format path for CSS (replace backslashes)
        css_path = path.replace("\\", "/")
        print(f"Setting background to: {css_path}")
        
        style = f"""
        QMainWindow {{
            background-image: url('{css_path}');
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
            background-size: cover;
        }} """
        
        # Combine with existing stylesheet
        self.setStyleSheet(STYLESHEET + style)

    @pyqtSlot()
    def open_mod_manager(self):
        # This ensures the dialog uses the main window's styles
        dialog = ModManagerDialog(self)
        dialog.exec()

    def populate_versions(self):
        self.status_label.setText("Loading versions...")
        self.version_combo.setEnabled(False)
        
        # --- CACHE: Try to load from cache first ---
        cached_versions = self.load_versions_from_cache()
        if cached_versions:
            self.version_combo.clear()
            self.version_combo.addItems(cached_versions)
            self.version_combo.setPlaceholderText("Select a version")
            self.status_label.setText("Ready (cached)")
            self.version_combo.setEnabled(True)
        else:
            self.status_label.setText("Fetching version list...")
            self.version_combo.setPlaceholderText("Loading...")
        # --- END CACHE ---

        # Start background fetch to get updates
        self.version_fetch_thread = QThread()
        self.version_fetcher = VersionFetcher()
        self.version_fetcher.moveToThread(self.version_fetch_thread)

        self.version_fetch_thread.started.connect(self.version_fetcher.run)
        self.version_fetcher.finished.connect(self._update_version_combo)
        
        self.version_fetcher.finished.connect(self.version_fetch_thread.quit)
        self.version_fetcher.finished.connect(self.version_fetcher.deleteLater)
        self.version_fetch_thread.finished.connect(self.version_fetch_thread.deleteLater)

        self.version_fetch_thread.start()

    @pyqtSlot(list, bool, str)
    def _update_version_combo(self, versions, success, message):
        if success:
            # Check if the new list is different from the one in the combo box
            current_versions = [self.version_combo.itemText(i) for i in range(self.version_combo.count())]
            
            if current_versions != versions:
                print("Updating version list from network...")
                current_selection = self.version_combo.currentText()
                self.version_combo.clear()
                self.version_combo.addItems(versions)
                
                # Try to restore previous selection
                index = self.version_combo.findText(current_selection)
                if index != -1:
                    self.version_combo.setCurrentIndex(index)
                    
                self.status_label.setText("Versions updated")
            else:
                print("Cached versions are up-to-date.")
                if not self.status_label.text().startswith("Ready"):
                    self.status_label.setText("Ready to launch")
            
            # Save the fresh list to cache
            self.save_versions_to_cache(versions)
            self.version_combo.setPlaceholderText("Select a version")
        
        else:
            # Only show error if we failed to load cache *and* network
            if self.version_combo.count() == 0:
                self.version_combo.setPlaceholderText("Failed to load")
                self.status_label.setText(message)
            
        self.version_combo.setEnabled(True)

    def load_versions_from_cache(self):
        if not os.path.exists(VERSIONS_CACHE_PATH):
            return None
        try:
            with open(VERSIONS_CACHE_PATH, 'r') as f:
                data = json.load(f)
                versions = data.get("release_versions", [])
                if versions:
                    print(f"Loaded {len(versions)} versions from cache.")
                    return versions
        except Exception as e:
            print(f"Error loading version cache: {e}")
            return None
        return None

    def save_versions_to_cache(self, versions):
        try:
            with open(VERSIONS_CACHE_PATH, 'w') as f:
                json.dump({"release_versions": versions}, f)
            print("Saved fresh versions to cache.")
        except Exception as e:
            print(f"Error saving version cache: {e}")

    @pyqtSlot()
    def start_launch(self):
        username = self.username_input.text().strip()
        version = self.version_combo.currentText()

        if not username:
            self.update_status("⚠️ Please enter a username")
            return
        if not version or version == "Loading versions...":
            self.update_status("⚠️ Please select a version")
            return
            
        use_fabric = self.fabric_toggle.isChecked()

        self.launch_button.setEnabled(False)
        self.launch_button.setText("⏳ LAUNCHING...")
        self.status_label.setText("Starting worker thread...")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        
        self.worker_thread = QThread()
        self.worker = Worker(version, username, use_fabric)
        self.worker.moveToThread(self.worker_thread)

        self.worker_thread.started.connect(self.worker.run)
        
        self.worker.progress.connect(self.update_progress)
        self.worker.status.connect(self.update_status)
        self.worker.finished.connect(self.on_launch_finished)
        
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)

        self.worker_thread.start()

    @pyqtSlot(int, int)
    def update_progress(self, value, max_value):
        if max_value == 0:
            self.progress_bar.setRange(0, 0)
            self.progress_bar.setFormat("Loading...")
        else:
            self.progress_bar.setRange(0, max_value)
            self.progress_bar.setValue(value)
            self.progress_bar.setFormat("%p%")

    @pyqtSlot(str)
    def update_status(self, message):
        self.status_label.setText(message)

    @pyqtSlot(bool, str)
    def on_launch_finished(self, success, message):
        self.launch_button.setEnabled(True)
        self.launch_button.setText("🚀 LAUNCH GAME")
        self.status_label.setText(message)
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(1 if success else 0)
        self.progress_bar.setFormat("%p%")
        
        if success and "Game closed" in message:
            self.progress_bar.setValue(0)
            self.status_label.setText("✓ Ready to launch")


# --- Main Execution ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    font = QFont("Segoe UI")
    if font.family() != "Segoe UI":
        font = QFont("Inter")
    font.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(font)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
