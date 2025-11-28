from PyQt6.QtCore import Qt, pyqtSlot, QThread, QSize, QTimer
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QGridLayout,
    QLabel,
    QScrollArea,
    QSpinBox,
)
import requests
import json

from .workers import ModDownloader, IconDownloader, ModSearchWorker
from .widgets import ModListItem, ModDetailDialog
from .modrinth_client import ModrinthClient

class ModBrowserPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.modrinth_client = ModrinthClient()
        self.search_results = []
        self.game_version = None
        self.loader = None
        self.threads = []
        self.current_search_id = 0

        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(175)
        self.search_timer.timeout.connect(self.start_search)

        self.init_ui()

    def set_launch_filters(self, version, loader):
        self.game_version = version if version and "Loading" not in version else None
        self.loader = loader

        if self.game_version or self.loader:
            filter_text = f"Filters: Version: {self.game_version or 'Any'}, Loader: {self.loader or 'Any'}"
            self.filter_status_label.setText(filter_text)
        else:
            self.filter_status_label.setText("No filters applied. Go to the Launch page to select a version.")

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Search bar
        search_container = QWidget()
        search_container.setObjectName("floating_search_container")
        search_layout = QVBoxLayout(search_container)
        search_layout.setContentsMargins(20, 20, 20, 20)

        search_bar_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search for mods on Modrinth...")
        self.search_input.setMinimumHeight(45)
        self.search_input.returnPressed.connect(self.start_search)
        self.search_input.textChanged.connect(self.on_search_text_changed)
        search_bar_layout.addWidget(self.search_input)

        self.limit_spinbox = QSpinBox()
        self.limit_spinbox.setRange(1, 100)
        self.limit_spinbox.setValue(20)
        self.limit_spinbox.setPrefix("Limit: ")
        self.limit_spinbox.setMinimumHeight(45)
        self.limit_spinbox.setFixedWidth(100)
        search_bar_layout.addWidget(self.limit_spinbox)

        self.search_button = QPushButton("Search")
        self.search_button.setObjectName("secondary_button")
        self.search_button.setMinimumHeight(45)
        self.search_button.clicked.connect(self.start_search)
        search_bar_layout.addWidget(self.search_button)
        search_layout.addLayout(search_bar_layout)

        self.filter_status_label = QLabel("No filters applied.")
        self.filter_status_label.setObjectName("status_label")
        search_layout.addWidget(self.filter_status_label, 0, Qt.AlignmentFlag.AlignRight)

        main_layout.addWidget(search_container)

        # Results grid
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setObjectName("content_scroll_area")
        main_layout.addWidget(scroll_area)

        results_container = QWidget()
        self.results_layout = QGridLayout(results_container)
        self.results_layout.setContentsMargins(20, 20, 20, 20)
        self.results_layout.setSpacing(20)
        scroll_area.setWidget(results_container)

    @pyqtSlot()
    def start_search(self):
        query = self.search_input.text().strip()
        if not query:
            return
        
        # If a thread is already running, we don't want to spam/lag by launching another one immediately
        # if we were strict. But the best UX is to cancel the old one (not possible easily) 
        # or just launch this one and ignore the old result.
        # Since 'requests' is blocking, the old thread will just finish eventually.
        # To prevent "lag", we just ensure we are on a thread.
        
        self.search_button.setText("Searching...")
        self.search_button.setEnabled(False)

        self.current_search_id += 1
        game_versions = [self.game_version] if self.game_version else None
        limit = self.limit_spinbox.value()

        thread = QThread()
        worker = ModSearchWorker(
            self.modrinth_client, 
            query, 
            game_versions, 
            self.loader, 
            limit,
            self.current_search_id
        )
        worker.moveToThread(thread)
        
        # Keep worker alive
        thread.worker = worker
        
        thread.started.connect(worker.run)
        worker.finished.connect(self.on_search_finished)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(lambda: self.threads.remove(thread) if thread in self.threads else None)
        
        self.threads.append(thread)
        thread.start()

    @pyqtSlot(list, int)
    def on_search_finished(self, results, search_id):
        if search_id != self.current_search_id:
            return
        
        self.search_results = results
        self.populate_results()
        self.search_button.setText("Search")
        self.search_button.setEnabled(True)

    @pyqtSlot(str)
    def on_search_text_changed(self, text):
        if self.search_timer.isActive():
            self.search_timer.stop()
        self.search_timer.start()

    def populate_results(self):
        # Clear existing results
        for i in reversed(range(self.results_layout.count())):
            self.results_layout.itemAt(i).widget().setParent(None)

        if not self.search_results:
            self.results_layout.addWidget(QLabel("No results found."), 0, 0, 1, 3)
            return

        row, col = 0, 0
        for mod in self.search_results:
            mod_card = ModListItem(mod, self.modrinth_client, self.game_version, self.loader)
            mod_card.card_clicked.connect(self.show_mod_detail)
            self.results_layout.addWidget(mod_card, row, col)

            col += 1
            if col == 3:
                col = 0
                row += 1

            icon_url = mod.get("icon_url")
            if icon_url:
                thread = QThread()
                downloader = IconDownloader(icon_url, mod.get("project_id"))
                downloader.moveToThread(thread)
                thread.started.connect(downloader.run)
                downloader.finished.connect(self.on_icon_downloaded)
                downloader.finished.connect(thread.quit)
                downloader.finished.connect(downloader.deleteLater)
                thread.finished.connect(thread.deleteLater)
                thread.start()
                self.threads.append(thread)

    @pyqtSlot(dict)
    def show_mod_detail(self, mod_data):
        dialog = ModDetailDialog(mod_data, self.modrinth_client, self)
        dialog.exec()
    @pyqtSlot(str, str)
    def on_icon_downloaded(self, mod_id, icon_path):
        if not icon_path:
            return

        for i in range(self.results_layout.count()):
            widget = self.results_layout.itemAt(i).widget()
            if isinstance(widget, ModListItem) and widget.mod_data.get("project_id") == mod_id:
                widget.set_icon(icon_path)
                break
