import glob
import json
import os
import shutil
from PyQt6 import sip
import uuid
from PyQt6.QtCore import QThread, pyqtSlot, Qt, QTimer, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QPoint
from PyQt6.QtGui import QColor, QFont, QCloseEvent
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSlider,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .constants import (
    APP_NAME,
    IMAGES_DIR,
    VERSIONS_CACHE_PATH,
    ICON_CACHE_DIR,
    MicrosoftInfo
)
from .mod_manager import ModsPage
from .stylesheet import STYLESHEET
from .workers import ImageDownloader, VersionFetcher, Worker
from .microsoft_auth import MicrosoftAuth
from .actions import setup_actions_and_menus
from .mod_browser import ModBrowserPage


class LaunchPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setObjectName("content_scroll_area")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        self.auth_method_label = QLabel("AUTHENTICATION")
        self.auth_method_label.setObjectName("section_label")
        layout.addWidget(self.auth_method_label)

        layout.addSpacing(5)

        self.auth_method_combo = QComboBox()
        self.auth_method_combo.addItems(["Offline", "Microsoft"])
        self.auth_method_combo.setMinimumHeight(55)
        layout.addWidget(self.auth_method_combo)

        layout.addSpacing(15)

        self.username_label = QLabel("USERNAME")
        self.username_label.setObjectName("section_label")
        layout.addWidget(self.username_label)

        layout.addSpacing(5)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.setText(f"Player{uuid.uuid4().hex[:6]}")
        self.username_input.setMinimumHeight(55)
        layout.addWidget(self.username_input)

        self.microsoft_login_button = QPushButton("Login with Microsoft")
        self.microsoft_login_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.microsoft_login_button.setMinimumHeight(55)
        layout.addWidget(self.microsoft_login_button)

        layout.addSpacing(15)

        version_label = QLabel("MINECRAFT VERSION")
        version_label.setObjectName("section_label")
        layout.addWidget(version_label)

        layout.addSpacing(5)

        self.version_combo = QComboBox()
        self.version_combo.setPlaceholderText("Loading versions...")
        self.version_combo.setMinimumHeight(55)
        layout.addWidget(self.version_combo)

        layout.addSpacing(15)

        mod_layout = QHBoxLayout()
        mod_layout.setSpacing(15)

        mod_loader_label = QLabel("MOD LOADER")
        mod_loader_label.setObjectName("section_label")
        mod_layout.addWidget(mod_loader_label, 0, Qt.AlignmentFlag.AlignVCenter)

        self.mod_loader_combo = QComboBox()
        self.mod_loader_combo.addItems(["Vanilla", "Fabric", "Forge", "NeoForge", "Quilt"])
        self.mod_loader_combo.setMinimumHeight(55)
        mod_layout.addWidget(self.mod_loader_combo)

        mod_layout.addStretch(1)

        self.mod_manager_button = QPushButton("Manage Mods")
        self.mod_manager_button.setObjectName("secondary_button")
        self.mod_manager_button.setCursor(Qt.CursorShape.PointingHandCursor)
        mod_layout.addWidget(self.mod_manager_button)

        layout.addLayout(mod_layout)

        layout.addSpacing(15)

        self.launch_button = QPushButton("🚀 LAUNCH GAME")
        self.launch_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.launch_button.setMinimumHeight(55)
        layout.addWidget(self.launch_button)

        layout.addSpacing(10)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setMinimumHeight(32)
        layout.addWidget(self.progress_bar)

        layout.addSpacing(5)

        self.status_label = QLabel("Ready to launch")
        self.status_label.setObjectName("status_label")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        layout.addStretch(1)

        scroll_area.setWidget(container)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.addWidget(scroll_area)


class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setObjectName("content_scroll_area")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Mods directory setting
        mods_dir_label = QLabel("MODS DIRECTORY")
        mods_dir_label.setObjectName("section_label")
        layout.addWidget(mods_dir_label)

        mods_dir_layout = QHBoxLayout()
        self.mods_dir_input = QLineEdit()
        self.mods_dir_input.setPlaceholderText("Enter mods directory path")
        self.mods_dir_input.setMinimumHeight(55)
        mods_dir_layout.addWidget(self.mods_dir_input)

        mods_dir_browse_button = QPushButton("Browse")
        mods_dir_browse_button.setObjectName("secondary_button")
        mods_dir_browse_button.setCursor(Qt.CursorShape.PointingHandCursor)
        mods_dir_browse_button.clicked.connect(lambda: self.browse_directory(self.mods_dir_input))
        mods_dir_layout.addWidget(mods_dir_browse_button)
        layout.addLayout(mods_dir_layout)

        # Images directory setting
        images_dir_label = QLabel("BACKGROUND IMAGES DIRECTORY")
        images_dir_label.setObjectName("section_label")
        layout.addWidget(images_dir_label)

        images_dir_layout = QHBoxLayout()
        self.images_dir_input = QLineEdit()
        self.images_dir_input.setPlaceholderText("Enter images directory path")
        self.images_dir_input.setMinimumHeight(55)
        images_dir_layout.addWidget(self.images_dir_input)

        images_dir_browse_button = QPushButton("Browse")
        images_dir_browse_button.setObjectName("secondary_button")
        images_dir_browse_button.setCursor(Qt.CursorShape.PointingHandCursor)
        images_dir_browse_button.clicked.connect(lambda: self.browse_directory(self.images_dir_input))
        images_dir_layout.addWidget(images_dir_browse_button)
        layout.addLayout(images_dir_layout)

        # Java executable setting
        java_executable_label = QLabel("JAVA EXECUTABLE (OPTIONAL)")
        java_executable_label.setObjectName("section_label")
        layout.addWidget(java_executable_label)

        java_executable_layout = QHBoxLayout()
        self.java_executable_input = QLineEdit()
        self.java_executable_input.setPlaceholderText("Enter Java executable path")
        self.java_executable_input.setMinimumHeight(55)
        java_executable_layout.addWidget(self.java_executable_input)

        java_executable_browse_button = QPushButton("Browse")
        java_executable_browse_button.setObjectName("secondary_button")
        java_executable_browse_button.setCursor(Qt.CursorShape.PointingHandCursor)
        java_executable_browse_button.clicked.connect(lambda: self.browse_file(self.java_executable_input))
        java_executable_layout.addWidget(java_executable_browse_button)
        layout.addLayout(java_executable_layout)

        # JVM arguments setting
        jvm_args_label = QLabel("JVM ARGUMENTS (ADVANCED)")
        jvm_args_label.setObjectName("section_label")
        layout.addWidget(jvm_args_label)

        self.jvm_args_input = QLineEdit()
        self.jvm_args_input.setPlaceholderText("-XX:+UnlockExperimentalVMOptions -XX:+UseG1GC")
        self.jvm_args_input.setMinimumHeight(55)
        layout.addWidget(self.jvm_args_input)

        # Memory allocation setting
        memory_label = QLabel("MEMORY ALLOCATION (RAM)")
        memory_label.setObjectName("section_label")
        layout.addWidget(memory_label)

        memory_layout = QHBoxLayout()
        self.memory_slider = QSlider(Qt.Orientation.Horizontal)
        self.memory_slider.setMinimum(1)
        self.memory_slider.setMaximum(16) # Assuming max 16GB, can be adjusted
        self.memory_slider.setValue(4) # Default 4GB
        self.memory_slider.setTickInterval(1)
        self.memory_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        memory_layout.addWidget(self.memory_slider)

        self.memory_value_label = QLabel("4 GB")
        self.memory_value_label.setObjectName("memory_label")
        self.memory_slider.valueChanged.connect(self.update_memory_label)
        memory_layout.addWidget(self.memory_value_label)
        layout.addLayout(memory_layout)

        # Resolution setting
        resolution_label = QLabel("GAME RESOLUTION")
        resolution_label.setObjectName("section_label")
        layout.addWidget(resolution_label)

        resolution_layout = QHBoxLayout()
        self.width_input = QLineEdit()
        self.width_input.setPlaceholderText("Width")
        self.width_input.setMinimumHeight(55)
        resolution_layout.addWidget(self.width_input)

        self.height_input = QLineEdit()
        self.height_input.setPlaceholderText("Height")
        self.height_input.setMinimumHeight(55)
        resolution_layout.addWidget(self.height_input)
        layout.addLayout(resolution_layout)

        layout.addStretch(1)

        save_button = QPushButton("Save Settings")
        save_button.setCursor(Qt.CursorShape.PointingHandCursor)
        save_button.setMinimumHeight(55)
        save_button.clicked.connect(self.save_settings)
        layout.addWidget(save_button)

        scroll_area.setWidget(container)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.addWidget(scroll_area)

        self.load_settings()

    def browse_file(self, line_edit):
        file, _ = QFileDialog.getOpenFileName(self, "Select File")
        if file:
            line_edit.setText(file)

    def update_memory_label(self, value):
        self.memory_value_label.setText(f"{value} GB")

    def browse_directory(self, line_edit):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            line_edit.setText(directory)

    def load_settings(self):
        if not os.path.exists("pymcl/config/settings.json"):
            return

        try:
            with open("pymcl/config/settings.json", "r") as f:
                settings = json.load(f)
                self.mods_dir_input.setText(settings.get("mods_dir", ""))
                self.images_dir_input.setText(settings.get("images_dir", ""))
                self.java_executable_input.setText(settings.get("java_executable", ""))
                self.jvm_args_input.setText(settings.get("jvm_arguments", ""))
                self.memory_slider.setValue(settings.get("memory_gb", 4))
                self.update_memory_label(self.memory_slider.value())
                resolution = settings.get("resolution", {})
                self.width_input.setText(resolution.get("width", ""))
                self.height_input.setText(resolution.get("height", ""))
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error loading settings: {e}")

    def save_settings(self):
        try:
            with open("pymcl/config/settings.json", "r+") as f:
                settings = json.load(f)
                settings["mods_dir"] = self.mods_dir_input.text().strip()
                settings["images_dir"] = self.images_dir_input.text().strip()
                settings["java_executable"] = self.java_executable_input.text().strip()
                settings["jvm_arguments"] = self.jvm_args_input.text().strip()
                settings["memory_gb"] = self.memory_slider.value()
                settings["resolution"] = {
                    "width": self.width_input.text().strip(),
                    "height": self.height_input.text().strip()
                }
                f.seek(0)
                json.dump(settings, f, indent=4)
                f.truncate()
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            os.makedirs("pymcl/config", exist_ok=True)
            with open("pymcl/config/settings.json", "w") as f:
                settings = {
                    "mods_dir": self.mods_dir_input.text().strip(),
                    "images_dir": self.images_dir_input.text().strip(),
                    "java_executable": self.java_executable_input.text().strip(),
                    "jvm_arguments": self.jvm_args_input.text().strip(),
                    "memory_gb": self.memory_slider.value(),
                    "resolution": {
                        "width": self.width_input.text().strip(),
                        "height": self.height_input.text().strip()
                    }
                }
                json.dump(settings, f, indent=4)
        QMessageBox.information(self, "Settings Saved", "Your settings have been saved. Some changes may require a restart to take effect.")


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
        self.current_background_style = ""
        self.last_version = None

        self.image_files = []
        self.current_image_index = 0

        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(900, 500)
        self.resize(1050, 650)

        self.microsoft_auth = MicrosoftAuth()
        self.microsoft_auth.login_success.connect(self.on_login_success)
        self.microsoft_auth.login_failed.connect(self.update_status)

        self.init_ui()
        self.load_settings()
        self.apply_styles()
        self.add_shadow_effects()
        self.populate_versions()
        self.init_background_images()
        self.load_microsoft_info()

        setup_actions_and_menus(self)

    def show(self):
        super().show()
        self.setWindowOpacity(0.0)
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(500)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.start()

    def load_settings(self):
        if not os.path.exists("pymcl/config/settings.json"):
            return

        try:
            with open("pymcl/config/settings.json", "r") as f:
                settings = json.load(f)
                last_username = settings.get("last_username", "")
                self.last_version = settings.get("last_version", "")
                if last_username:
                    self.launch_page.username_input.setText(last_username)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error loading settings: {e}")

    def init_ui(self):
        central_widget = QWidget()
        central_widget.setObjectName("main_central_widget")
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Left navigation
        left_widget = QWidget()
        left_widget.setObjectName("left_title_container")
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(5)
        left_layout.setContentsMargins(10, 10, 10, 10)

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

        self.nav_launch_button = QPushButton("Launch")
        self.nav_launch_button.setObjectName("nav_button_active")
        self.nav_launch_button.setCursor(Qt.CursorShape.PointingHandCursor)
        left_layout.addWidget(self.nav_launch_button)

        self.nav_mods_button = QPushButton("Mods")
        self.nav_mods_button.setObjectName("nav_button")
        self.nav_mods_button.setCursor(Qt.CursorShape.PointingHandCursor)
        left_layout.addWidget(self.nav_mods_button)

        self.nav_browse_mods_button = QPushButton("Browse Mods")
        self.nav_browse_mods_button.setObjectName("nav_button")
        self.nav_browse_mods_button.setCursor(Qt.CursorShape.PointingHandCursor)
        left_layout.addWidget(self.nav_browse_mods_button)

        self.nav_settings_button = QPushButton("Settings")
        self.nav_settings_button.setObjectName("nav_button")
        self.nav_settings_button.setCursor(Qt.CursorShape.PointingHandCursor)
        left_layout.addWidget(self.nav_settings_button)

        left_layout.addStretch(1)
        main_layout.addWidget(left_widget, 2)

        # Right content
        content_frame = QFrame()
        content_frame.setObjectName("central_widget_frame")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        main_layout.addWidget(content_frame, 3)

        self.stacked_widget = QStackedWidget()
        content_layout.addWidget(self.stacked_widget)

        self.launch_page = LaunchPage()
        self.settings_page = SettingsPage()
        self.mods_page = ModsPage()
        self.mod_browser_page = ModBrowserPage()

        self.stacked_widget.addWidget(self.launch_page)
        self.stacked_widget.addWidget(self.mods_page)
        self.stacked_widget.addWidget(self.mod_browser_page)
        self.stacked_widget.addWidget(self.settings_page)

        self.nav_launch_button.clicked.connect(lambda: self.switch_page(0, self.nav_launch_button))
        self.nav_mods_button.clicked.connect(lambda: self.switch_page(1, self.nav_mods_button))
        self.nav_browse_mods_button.clicked.connect(lambda: self.switch_page(2, self.nav_browse_mods_button))
        self.nav_settings_button.clicked.connect(lambda: self.switch_page(3, self.nav_settings_button))

        # Connect signals from launch page to main window slots
        self.launch_page.username_input.textChanged.connect(self.save_settings)
        self.launch_page.auth_method_combo.currentTextChanged.connect(self.update_auth_widgets)
        self.launch_page.microsoft_login_button.clicked.connect(self.start_microsoft_login)
        self.launch_page.launch_button.clicked.connect(self.start_launch)
        self.launch_page.mod_manager_button.clicked.connect(self.open_mod_manager)

        self.update_auth_widgets()

    def switch_page(self, index, button):
        current_index = self.stacked_widget.currentIndex()
        if index == current_index:
            return

        # Pass launch options to mod browser
        if self.stacked_widget.widget(index) == self.mod_browser_page:
            version = self.launch_page.version_combo.currentText()
            mod_loader = self.launch_page.mod_loader_combo.currentText()
            loader_param = None
            if mod_loader == "Fabric":
                loader_param = "fabric"
            # Add conditions for other loaders if Modrinth API supports them
            # For now, only Fabric is directly mapped
            self.mod_browser_page.set_launch_filters(version, loader_param)

        # Update nav button styles
        for btn in [self.nav_launch_button, self.nav_mods_button, self.nav_browse_mods_button, self.nav_settings_button]:
            btn.setObjectName("nav_button")
        button.setObjectName("nav_button_active")
        self.apply_styles()

        # Animation
        self.slide_animation = self._create_slide_animation(index, current_index)
        self.slide_animation.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

    def _create_slide_animation(self, new_index, old_index):
        width = self.stacked_widget.width()

        # New widget to slide in
        new_widget = self.stacked_widget.widget(new_index)
        new_widget.setGeometry(0, 0, width, self.stacked_widget.height())
        new_widget.move(width if new_index > old_index else -width, 0)
        new_widget.show()
        new_widget.raise_()

        anim_new = QPropertyAnimation(new_widget, b"pos")
        anim_new.setDuration(300)
        anim_new.setEndValue(self.stacked_widget.rect().topLeft())
        anim_new.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Old widget to slide out
        old_widget = self.stacked_widget.widget(old_index)
        anim_old = QPropertyAnimation(old_widget, b"pos")
        anim_old.setDuration(300)
        anim_old.setEndValue(QPoint(width if new_index < old_index else -width, 0))
        anim_old.setEasingCurve(QEasingCurve.Type.OutCubic)

        anim_group = QParallelAnimationGroup()
        anim_group.addAnimation(anim_new)
        anim_group.addAnimation(anim_old)

        anim_group.finished.connect(lambda: self.on_animation_finished(new_index, old_widget))
        return anim_group

    def on_animation_finished(self, new_index, old_widget):
        self.stacked_widget.setCurrentIndex(new_index)
        old_widget.hide()
        old_widget.move(0, 0)

    def update_auth_widgets(self):
        auth_method = self.launch_page.auth_method_combo.currentText()
        if auth_method == "Offline":
            self.launch_page.username_label.setVisible(True)
            self.launch_page.username_input.setVisible(True)
            self.launch_page.microsoft_login_button.setVisible(False)
        elif auth_method == "Microsoft":
            self.launch_page.username_label.setVisible(False)
            self.launch_page.username_input.setVisible(False)
            self.launch_page.microsoft_login_button.setVisible(True)

    def start_microsoft_login(self):
        self.microsoft_auth.start_login()

    def on_login_success(self, info: MicrosoftInfo):
        self.minecraft_info = info
        self.update_status(f"Logged in as {info['username']}")
        self.launch_page.microsoft_login_button.setText(f"Logged in as {info['username']}")

    def load_microsoft_info(self):
        info = self.microsoft_auth.load_microsoft_info()
        if info:
            if self.microsoft_auth.is_token_expired():
                self.update_status("Refreshing token...")
                info = self.microsoft_auth.refresh_token()

            if info:
                self.minecraft_info = info
                self.update_status(f"Logged in as {info['username']}")
                self.launch_page.microsoft_login_button.setText(f"Logged in as {info['username']}")
                self.launch_page.auth_method_combo.setCurrentText("Microsoft")
            else:
                self.update_status("Failed to refresh token. Please login again.")

    def apply_styles(self):
        self.setStyleSheet(STYLESHEET + self.current_background_style)

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

        self.current_background_style = f"""
        QMainWindow {{
            background-image: url('{css_path}');
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }} """

        self.apply_styles()

    @pyqtSlot()
    def open_mod_manager(self):
        self.switch_page(1, self.nav_mods_button)

    def populate_versions(self):
        self.launch_page.status_label.setText("Loading versions...")
        self.launch_page.version_combo.setEnabled(False)

        cached_versions = self.load_versions_from_cache()
        if cached_versions:
            self.launch_page.version_combo.clear()
            self.launch_page.version_combo.addItems(cached_versions)
            
            if self.last_version and self.last_version in cached_versions:
                index = self.launch_page.version_combo.findText(self.last_version)
                if index != -1:
                    self.launch_page.version_combo.setCurrentIndex(index)
            
            self.launch_page.version_combo.setPlaceholderText("Select a version")
            self.launch_page.status_label.setText("Ready (versions fetched from cache)")
            self.launch_page.version_combo.setEnabled(True)
        else:
            self.launch_page.status_label.setText("Fetching version list...")
            self.launch_page.version_combo.setPlaceholderText("Loading...")

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
                self.launch_page.version_combo.itemText(i)
                for i in range(self.launch_page.version_combo.count())
            ]

            if current_versions != versions:
                print("Updating version list from network...")
                current_selection = self.launch_page.version_combo.currentText()
                self.launch_page.version_combo.clear()
                self.launch_page.version_combo.addItems(versions)

                # Restore previous selection or load last played version
                if current_selection and current_selection in versions:
                     index = self.launch_page.version_combo.findText(current_selection)
                     if index != -1:
                         self.launch_page.version_combo.setCurrentIndex(index)
                elif self.last_version and self.last_version in versions:
                     index = self.launch_page.version_combo.findText(self.last_version)
                     if index != -1:
                         self.launch_page.version_combo.setCurrentIndex(index)

                self.launch_page.status_label.setText("Versions updated")
            else:
                print("Cached versions are up-to-date.")
                if not self.launch_page.status_label.text().startswith("Ready"):
                    self.launch_page.status_label.setText("Ready to launch")

            self.save_versions_to_cache(versions)
            self.launch_page.version_combo.setPlaceholderText("Select a version")

        else:
            if self.launch_page.version_combo.count() == 0:
                self.launch_page.version_combo.setPlaceholderText("Failed to load")
                self.launch_page.status_label.setText(message)

        self.launch_page.version_combo.setEnabled(True)

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

    def save_settings(self):
        try:
            with open("pymcl/config/settings.json", "r+") as f:
                settings = json.load(f)
                settings["last_username"] = self.launch_page.username_input.text().strip()
                settings["last_version"] = self.launch_page.version_combo.currentText()
                f.seek(0)
                json.dump(settings, f, indent=4)
                f.truncate()
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            # Config file or directory might not exist yet, create it
            os.makedirs("pymcl/config", exist_ok=True)
            with open("pymcl/config/settings.json", "w") as f:
                settings = {
                    "last_username": self.launch_page.username_input.text().strip(),
                    "last_version": self.launch_page.version_combo.currentText()
                }
                json.dump(settings, f, indent=4)
    @pyqtSlot()
    def start_launch(self):
        auth_method = self.launch_page.auth_method_combo.currentText()
        version = self.launch_page.version_combo.currentText()
        mod_loader_type = self.launch_page.mod_loader_combo.currentText()

        if not version or version == "Loading versions...":
            self.update_status("⚠️ Please select a version")
            return

        # Load settings to pass to the worker
        settings = {}
        if os.path.exists("pymcl/config/settings.json"):
            try:
                with open("pymcl/config/settings.json", "r") as f:
                    settings = json.load(f)
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error loading settings for launch: {e}")

        options = {
            "username": "",
            "uuid": "",
            "token": "",
            "executablePath": settings.get("java_executable"),
            "jvmArguments": settings.get("jvm_arguments", "").split(),
            "resolutionWidth": settings.get("resolution", {}).get("width"),
            "resolutionHeight": settings.get("resolution", {}).get("height"),
        }

        memory_gb = settings.get("memory_gb", 4)
        options["jvmArguments"].append(f"-Xmx{memory_gb}G")
        options["jvmArguments"].append(f"-Xms{memory_gb}G")

        if auth_method == "Offline":
            username = self.launch_page.username_input.text().strip()
            if not username:
                self.update_status("⚠️ Please enter a username")
                return
            options["username"] = username
            options["uuid"] = str(uuid.uuid4())
            self.save_settings()
        elif auth_method == "Microsoft":
            if not self.minecraft_info:
                self.update_status("⚠️ Please login with Microsoft")
                return
            options["username"] = self.minecraft_info["username"]
            options["uuid"] = self.minecraft_info["uuid"]
            options["token"] = self.minecraft_info["access_token"]
            self.save_settings()

        self.launch_page.launch_button.setEnabled(False)
        self.launch_page.launch_button.setText("⏳ LAUNCHING...")
        self.launch_page.status_label.setText("Starting worker thread...")
        self.launch_page.progress_bar.setRange(0, 100)
        self.launch_page.progress_bar.setValue(0)

        self.worker_thread = QThread()
        self.worker = Worker(version, options, mod_loader_type)
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
            self.launch_page.progress_bar.setRange(0, 0)
            self.launch_page.progress_bar.setFormat("Loading...")
        else:
            self.launch_page.progress_bar.setRange(0, max_value)
            self.launch_page.progress_bar.setValue(value)
            self.launch_page.progress_bar.setFormat("%p%")

    @pyqtSlot(str)
    def update_status(self, message):
        self.launch_page.status_label.setText(message)

    @pyqtSlot(bool, str)
    def on_launch_finished(self, success, message):
        self.launch_page.launch_button.setEnabled(True)
        self.launch_page.launch_button.setText("🚀 LAUNCH GAME")
        self.launch_page.status_label.setText(message)
        self.launch_page.progress_bar.setRange(0, 1)
        self.launch_page.progress_bar.setValue(1 if success else 0)
        self.launch_page.progress_bar.setFormat("%p%")

        if success and "Game closed" in message:
            self.launch_page.progress_bar.setValue(0)
            self.launch_page.status_label.setText("✓ Ready to launch")

    def clear_cache(self):
        try:
            if os.path.exists(ICON_CACHE_DIR):
                shutil.rmtree(ICON_CACHE_DIR)
                QMessageBox.information(self, "Cache Cleared", "The icon cache has been cleared.")
            else:
                QMessageBox.information(self, "Cache Cleared", "No icon cache to clear.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not clear cache: {e}")

    def clear_cache(self):
        try:
            if os.path.exists(ICON_CACHE_DIR):
                shutil.rmtree(ICON_CACHE_DIR)
                QMessageBox.information(self, "Cache Cleared", "The icon cache has been cleared.")
            else:
                QMessageBox.information(self, "Cache Cleared", "No icon cache to clear.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not clear cache: {e}")

    def closeEvent(self, a0: QCloseEvent | None):
        if self.bg_timer:
            self.bg_timer.stop()

        if hasattr(self, 'worker_thread') and self.worker_thread and not sip.isdeleted(self.worker_thread) and self.worker_thread.isRunning():
            self.worker_thread.quit()
            self.worker_thread.wait()

        if hasattr(self, 'version_fetch_thread') and self.version_fetch_thread and not sip.isdeleted(self.version_fetch_thread) and self.version_fetch_thread.isRunning():
            self.version_fetch_thread.quit()
            self.version_fetch_thread.wait()

        if hasattr(self, 'image_downloader_thread') and self.image_downloader_thread and not sip.isdeleted(self.image_downloader_thread) and self.image_downloader_thread.isRunning():
            self.image_downloader_thread.quit()
            self.image_downloader_thread.wait()

        if a0 is not None:
            a0.accept()
        else:
            super().closeEvent(a0)