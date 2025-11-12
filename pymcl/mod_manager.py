import glob
import os

from PyQt6.QtCore import QThread, pyqtSlot, Qt, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from .constants import MODS_DIR
from .widgets import ModListWidget
from .workers import ModDownloader

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

        drop_label = QLabel("Drag & Drop .jar files here to install them")
        drop_label.setObjectName("section_label")
        drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(drop_label)

        self.mod_list_widget = ModListWidget()
        self.mod_list_widget.mods_changed.connect(self.populate_mods_list)
        layout.addWidget(self.mod_list_widget, 1)

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

        self.download_status_label = QLabel("")
        self.download_status_label.setObjectName("status_label")
        layout.addWidget(self.download_status_label)

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
                item.setData(Qt.ItemDataRole.UserRole, mod_path)
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

        reply = QMessageBox.question(
            self,
            "Delete Mod",
            f"Are you sure you want to delete '{filename}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

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

