import glob
import json
import os
import uuid
from PyQt6.QtCore import QThread, pyqtSlot, Qt, QTimer
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .constants import (
    APP_NAME,
    IMAGES_DIR,
    VERSIONS_CACHE_PATH,
    MicrosoftInfo
)
from .mod_manager import ModManagerDialog
from .stylesheet import STYLESHEET
from .workers import ImageDownloader, VersionFetcher, Worker
from .microsoft_auth import MicrosoftAuth


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
        self.minecraft_info: MicrosoftInfo | None = None

        self.image_files = []
        self.current_image_index = 0

        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(900, 500)
        self.resize(1000, 600)

        self.microsoft_auth = MicrosoftAuth()
        self.microsoft_auth.login_success.connect(self.on_login_success)
        self.microsoft_auth.login_failed.connect(self.update_status)

        self.init_ui()
        self.apply_styles()
        self.add_shadow_effects()
        self.populate_versions()
        self.init_background_images()
        self.load_microsoft_info()

    def init_ui(self):
        central_widget = QWidget()
        central_widget.setObjectName("main_central_widget")
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(40)

        left_widget = QWidget()
        left_widget.setObjectName("left_title_container")
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(5)
        left_layout.setContentsMargins(0, 0, 0, 0)

        title_frame = QFrame()
        title_frame.setObjectName("title_frame")
        title_frame_layout = QVBoxLayout(title_frame)
        title_frame_layout.setSpacing(0)
        title_frame_layout.setContentsMargins(20, 20, 20, 20)

        title_label = QLabel(APP_NAME)
        title_label.setObjectName("title_label")
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        title_frame_layout.addWidget(title_label)

        subtitle_label = QLabel("Offline Minecraft Launcher")
        subtitle_label.setObjectName("subtitle_label")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        title_frame_layout.addWidget(subtitle_label)

        left_layout.addWidget(title_frame)
        left_layout.addStretch(1)
        main_layout.addWidget(left_widget, 2)

        content_frame = QFrame()
        content_frame.setObjectName("central_widget_frame")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(40, 40, 40, 40)
        content_layout.setSpacing(0)
        main_layout.addWidget(content_frame, 3)

        auth_method_label = QLabel("AUTHENTICATION")
        auth_method_label.setObjectName("section_label")
        content_layout.addWidget(auth_method_label)

        content_layout.addSpacing(5)

        self.auth_method_combo = QComboBox()
        self.auth_method_combo.addItems(["Offline", "Microsoft"])
        self.auth_method_combo.setMinimumHeight(55)
        self.auth_method_combo.currentTextChanged.connect(self.update_auth_widgets)
        content_layout.addWidget(self.auth_method_combo)

        content_layout.addSpacing(20)

        self.username_label = QLabel("USERNAME")
        self.username_label.setObjectName("section_label")
        content_layout.addWidget(self.username_label)

        content_layout.addSpacing(5)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.setText(f"Player{uuid.uuid4().hex[:6]}")
        self.username_input.setMinimumHeight(55)
        content_layout.addWidget(self.username_input)

        self.microsoft_login_button = QPushButton("Login with Microsoft")
        self.microsoft_login_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.microsoft_login_button.setMinimumHeight(55)
        self.microsoft_login_button.clicked.connect(self.start_microsoft_login)
        content_layout.addWidget(self.microsoft_login_button)

        content_layout.addSpacing(20)

        version_label = QLabel("MINECRAFT VERSION")
        version_label.setObjectName("section_label")
        content_layout.addWidget(version_label)

        content_layout.addSpacing(5)

        self.version_combo = QComboBox()
        self.version_combo.setPlaceholderText("Loading versions...")
        self.version_combo.setMinimumHeight(55)
        content_layout.addWidget(self.version_combo)

        content_layout.addSpacing(20)

        mod_layout = QHBoxLayout()
        mod_layout.setSpacing(15)

        self.fabric_toggle = QCheckBox("Use Fabric")
        mod_layout.addWidget(self.fabric_toggle, 0, Qt.AlignmentFlag.AlignVCenter)

        mod_layout.addStretch(1)

        self.mod_manager_button = QPushButton("Manage Mods")
        self.mod_manager_button.setObjectName("secondary_button")
        self.mod_manager_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mod_manager_button.clicked.connect(self.open_mod_manager)
        mod_layout.addWidget(self.mod_manager_button)

        content_layout.addLayout(mod_layout)

        content_layout.addSpacing(20)

        self.launch_button = QPushButton("🚀 LAUNCH GAME")
        self.launch_button.clicked.connect(self.start_launch)
        self.launch_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.launch_button.setMinimumHeight(55)
        content_layout.addWidget(self.launch_button)

        content_layout.addSpacing(15)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setMinimumHeight(32)
        content_layout.addWidget(self.progress_bar)

        content_layout.addSpacing(5)

        self.status_label = QLabel("Ready to launch")
        self.status_label.setObjectName("status_label")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(self.status_label)

        content_layout.addStretch(1)
        self.update_auth_widgets()

    def update_auth_widgets(self):
        auth_method = self.auth_method_combo.currentText()
        if auth_method == "Offline":
            self.username_label.setVisible(True)
            self.username_input.setVisible(True)
            self.microsoft_login_button.setVisible(False)
        elif auth_method == "Microsoft":
            self.username_label.setVisible(False)
            self.username_input.setVisible(False)
            self.microsoft_login_button.setVisible(True)

    def start_microsoft_login(self):
        self.microsoft_auth.start_login()

    def on_login_success(self, info: MicrosoftInfo):
        self.minecraft_info = info
        self.update_status(f"Logged in as {info['username']}")
        self.microsoft_login_button.setText(f"Logged in as {info['username']}")

    def load_microsoft_info(self):
        info = self.microsoft_auth.load_microsoft_info()
        if info:
            if self.microsoft_auth.is_token_expired():
                self.update_status("Refreshing token...")
                info = self.microsoft_auth.refresh_token()

            if info:
                self.minecraft_info = info
                self.update_status(f"Logged in as {info['username']}")
                self.microsoft_login_button.setText(f"Logged in as {info['username']}")
                self.auth_method_combo.setCurrentText("Microsoft")
            else:
                self.update_status("Failed to refresh token. Please login again.")

    def apply_styles(self):
        self.setStyleSheet(STYLESHEET)

    def add_shadow_effects(self):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 5)
        self.findChild(QFrame, "central_widget_frame").setGraphicsEffect(shadow)

        title_shadow = QGraphicsDropShadowEffect()
        title_shadow.setBlurRadius(20)
        title_shadow.setColor(QColor(0, 0, 0, 80))
        title_shadow.setOffset(0, 3)
        self.findChild(QFrame, "title_frame").setGraphicsEffect(title_shadow)

    def init_background_images(self):
        print("Initializing background images...")
        self.image_files = glob.glob(os.path.join(IMAGES_DIR, "*.png")) + glob.glob(
            os.path.join(IMAGES_DIR, "*.jpg")
        )

        if not self.image_files:
            print("No images found. Downloading default image.")
            self.image_downloader_thread = QThread()
            self.image_downloader = ImageDownloader()
            self.image_downloader.moveToThread(self.image_downloader_thread)

            self.image_downloader_thread.started.connect(self.image_downloader.run)
            self.image_downloader.finished.connect(self.on_image_downloaded)

            self.image_downloader.finished.connect(self.image_downloader_thread.quit)
            self.image_downloader.finished.connect(self.image_downloader.deleteLater)
            self.image_downloader_thread.finished.connect(
                self.image_downloader_thread.deleteLater
            )

            self.image_downloader_thread.start()
        else:
            print(f"Found {len(self.image_files)} images.")
            self.update_background_image()

            if len(self.image_files) > 1:
                print("Starting background image timer...")
                self.bg_timer = QTimer(self)
                self.bg_timer.timeout.connect(self.update_background_image)
                self.bg_timer.start(30000)

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
        self.current_image_index = (self.current_image_index + 1) % len(
            self.image_files
        )

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

        self.setStyleSheet(STYLESHEET + style)

    @pyqtSlot()
    def open_mod_manager(self):
        dialog = ModManagerDialog(self)
        dialog.exec()

    def populate_versions(self):
        self.status_label.setText("Loading versions...")
        self.version_combo.setEnabled(False)

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

        self.version_fetch_thread = QThread()
        self.version_fetcher = VersionFetcher()
        self.version_fetcher.moveToThread(self.version_fetch_thread)

        self.version_fetch_thread.started.connect(self.version_fetcher.run)
        self.version_fetcher.finished.connect(self._update_version_combo)

        self.version_fetcher.finished.connect(self.version_fetch_thread.quit)
        self.version_fetcher.finished.connect(self.version_fetcher.deleteLater)
        self.version_fetch_thread.finished.connect(
            self.version_fetch_thread.deleteLater
        )

        self.version_fetch_thread.start()

    @pyqtSlot(list, bool, str)
    def _update_version_combo(self, versions, success, message):
        if success:
            current_versions = [
                self.version_combo.itemText(i)
                for i in range(self.version_combo.count())
            ]

            if current_versions != versions:
                print("Updating version list from network...")
                current_selection = self.version_combo.currentText()
                self.version_combo.clear()
                self.version_combo.addItems(versions)

                index = self.version_combo.findText(current_selection)
                if index != -1:
                    self.version_combo.setCurrentIndex(index)

                self.status_label.setText("Versions updated")
            else:
                print("Cached versions are up-to-date.")
                if not self.status_label.text().startswith("Ready"):
                    self.status_label.setText("Ready to launch")

            self.save_versions_to_cache(versions)
            self.version_combo.setPlaceholderText("Select a version")

        else:
            if self.version_combo.count() == 0:
                self.version_combo.setPlaceholderText("Failed to load")
                self.status_label.setText(message)

        self.version_combo.setEnabled(True)

    def load_versions_from_cache(self):
        if not os.path.exists(VERSIONS_CACHE_PATH):
            return None
        try:
            with open(VERSIONS_CACHE_PATH, "r") as f:
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
            with open(VERSIONS_CACHE_PATH, "w") as f:
                json.dump({"release_versions": versions}, f)
            print("Saved fresh versions to cache.")
        except Exception as e:
            print(f"Error saving version cache: {e}")

    @pyqtSlot()
    def start_launch(self):
        auth_method = self.auth_method_combo.currentText()
        version = self.version_combo.currentText()
        use_fabric = self.fabric_toggle.isChecked()

        if not version or version == "Loading versions...":
            self.update_status("⚠️ Please select a version")
            return

        options = {
            "username": "",
            "uuid": "",
            "token": ""
        }

        if auth_method == "Offline":
            username = self.username_input.text().strip()
            if not username:
                self.update_status("⚠️ Please enter a username")
                return
            options["username"] = username
            options["uuid"] = str(uuid.uuid4())
        elif auth_method == "Microsoft":
            if not self.minecraft_info:
                self.update_status("⚠️ Please login with Microsoft")
                return
            options["username"] = self.minecraft_info["username"]
            options["uuid"] = self.minecraft_info["uuid"]
            options["token"] = self.minecraft_info["access_token"]

        self.launch_button.setEnabled(False)
        self.launch_button.setText("⏳ LAUNCHING...")
        self.status_label.setText("Starting worker thread...")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        self.worker_thread = QThread()
        self.worker = Worker(version, options, use_fabric)
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
