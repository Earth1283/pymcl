import glob
import os
import shutil

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
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from .constants import MODS_DIR, ICON_CACHE_DIR
from .widgets import ModListWidget, InstalledModItem
from .workers import ModDownloader, UpdateCheckerWorker
from .modrinth_client import ModrinthClient

class ModsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.downloader_thread = None
        self.downloader = None
        self.modrinth_client = ModrinthClient()
        self.update_thread = None

        self.init_ui()
        self.populate_mods_list()

    def init_ui(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setObjectName("content_scroll_area")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Update check button
        self.check_updates_button = QPushButton("Check for Mod Updates")
        self.check_updates_button.setObjectName("secondary_button")
        self.check_updates_button.clicked.connect(self.check_updates)
        layout.addWidget(self.check_updates_button)

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

        open_folder_button = QPushButton("Mods Folder")
        open_folder_button.setObjectName("secondary_button")
        open_folder_button.clicked.connect(self.open_mods_folder)
        button_layout.addWidget(open_folder_button)

        delete_button = QPushButton("Delete")
        delete_button.setObjectName("danger_button")
        delete_button.clicked.connect(self.delete_selected_mod)
        button_layout.addWidget(delete_button)

        button_layout.addStretch(1)

        clear_cache_button = QPushButton("Clear Icon Cache")
        clear_cache_button.setObjectName("secondary_button")
        clear_cache_button.clicked.connect(self.clear_cache)
        button_layout.addWidget(clear_cache_button)

        refresh_button = QPushButton("Refresh")
        refresh_button.setObjectName("secondary_button")
        refresh_button.clicked.connect(self.populate_mods_list)
        button_layout.addWidget(refresh_button)

        layout.addLayout(button_layout)

        scroll_area.setWidget(container)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.addWidget(scroll_area)

    @pyqtSlot()
    def check_updates(self):
        print("--- Starting mod update check ---")
        self.check_updates_button.setEnabled(False)
        self.check_updates_button.setText("Checking for updates...")
        
        self.update_thread = QThread()
        self.update_worker = UpdateCheckerWorker(self.modrinth_client)
        self.update_worker.moveToThread(self.update_thread)
        
        self.update_thread.started.connect(self.update_worker.run)
        self.update_worker.finished.connect(self.on_updates_found)
        self.update_worker.finished.connect(self.update_thread.quit)
        self.update_worker.finished.connect(self.update_worker.deleteLater)
        self.update_thread.finished.connect(self.update_thread.deleteLater)
        
        self.update_thread.start()
        print("UpdateCheckerWorker started.")

    @pyqtSlot(dict)
    def on_updates_found(self, updates):
        self.check_updates_button.setEnabled(True)
        self.check_updates_button.setText("Check for Mod Updates")
        
        count = 0
        for i in range(self.mod_list_widget.count()):
            item = self.mod_list_widget.item(i)
            mod_path = item.data(Qt.ItemDataRole.UserRole)
            widget = self.mod_list_widget.itemWidget(item)
            
            if mod_path in updates and isinstance(widget, InstalledModItem):
                widget.show_update(updates[mod_path])
                count += 1
                
        if count > 0:
            self.download_status_label.setText(f"Found {count} available updates!")
        else:
            self.download_status_label.setText("All mods are up to date.")

    @pyqtSlot(str, dict)
    def on_update_mod(self, old_path, new_version_data):
        # This handles the click on "UPDATE AVAILABLE"
        files = new_version_data.get("files", [])
        primary_file = next((f for f in files if f.get("primary")), files[0] if files else None)
        
        if not primary_file:
            QMessageBox.warning(self, "Error", "Could not find file to download for update.")
            return
            
        url = primary_file.get("url")
        if not url:
            return

        # Delete old file
        try:
            if os.path.exists(old_path):
                os.remove(old_path)
        except Exception as e:
             print(f"Error removing old mod: {e}")
             
        # Start download of new one
        self.url_input.setText(url)
        self.start_mod_download()


    @pyqtSlot()
    def clear_cache(self):
        try:
            if os.path.exists(ICON_CACHE_DIR):
                shutil.rmtree(ICON_CACHE_DIR)
                self.download_status_label.setText("Icon cache cleared.")
            else:
                self.download_status_label.setText("No icon cache to clear.")
        except Exception as e:
            self.download_status_label.setText(f"Error clearing cache: {e}")

    @pyqtSlot()
    def populate_mods_list(self):
        self.mod_list_widget.clear()
        try:
            jar_files = glob.glob(os.path.join(MODS_DIR, "*.jar"))
            for mod_path in jar_files:
                item = QListWidgetItem()
                # We don't set text on item, because we use setItemWidget
                item.setData(Qt.ItemDataRole.UserRole, mod_path)
                
                widget = InstalledModItem(mod_path)
                widget.update_clicked.connect(self.on_update_mod)
                
                item.setSizeHint(widget.sizeHint())
                self.mod_list_widget.addItem(item)
                self.mod_list_widget.setItemWidget(item, widget)
                
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

