from PyQt6.QtCore import Qt, pyqtSlot, QThread
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QTextEdit,
    QSplitter,
    QComboBox,
)
import requests
import json

from .workers import ModDownloader

class ModrinthClient:
    BASE_URL = "https://api.modrinth.com/v2"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "PyMCL/1.0 (github.com/sonnynomnom/PyMCL)"}
        )

    def search(self, query, game_versions=None, loader=None):
        params = {"query": query, "limit": 20}
        facets = []
        if game_versions:
            facets.append([f"versions:{v}" for v in game_versions])
        if loader:
            # Modrinth uses 'categories' for loaders in facets
            facets.append([f"categories:{loader}"])
        
        if facets:
            params["facets"] = json.dumps(facets)
            
        try:
            response = self.session.get(f"{self.BASE_URL}/search", params=params)
            response.raise_for_status()
            return response.json().get("hits", [])
        except requests.RequestException as e:
            print(f"Error searching Modrinth: {e}")
            return []

    def get_versions(self, mod_id, game_versions=None, loader=None):
        params = {}
        if game_versions:
            params["game_versions"] = json.dumps(game_versions)
        if loader:
            params["loaders"] = json.dumps([loader])
            
        try:
            response = self.session.get(f"{self.BASE_URL}/project/{mod_id}/version", params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error getting versions from Modrinth: {e}")
            return []

class ModBrowserPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.modrinth_client = ModrinthClient()
        self.search_results = []
        self.game_version = None
        self.loader = None

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

        # Search bar
        search_container = QWidget()
        search_layout = QVBoxLayout(search_container)
        search_layout.setContentsMargins(20, 20, 20, 10)
        
        search_bar_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search for mods on Modrinth...")
        self.search_input.setMinimumHeight(45)
        self.search_input.returnPressed.connect(self.start_search)
        search_bar_layout.addWidget(self.search_input)

        self.search_button = QPushButton("Search")
        self.search_button.setObjectName("secondary_button")
        self.search_button.setMinimumHeight(45)
        self.search_button.clicked.connect(self.start_search)
        search_bar_layout.addWidget(self.search_button)
        search_layout.addLayout(search_bar_layout)
        
        self.filter_status_label = QLabel("No filters applied.")
        self.filter_status_label.setObjectName("status_label")
        search_layout.addWidget(self.filter_status_label)
        
        main_layout.addWidget(search_container)

        # Content splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter, 1)

        # Search results list
        results_widget = QWidget()
        results_layout = QVBoxLayout(results_widget)
        results_layout.setContentsMargins(20, 0, 10, 20)
        results_label = QLabel("SEARCH RESULTS")
        results_label.setObjectName("section_label")
        results_layout.addWidget(results_label)
        
        self.results_list = QListWidget()
        self.results_list.itemSelectionChanged.connect(self.on_mod_selected)
        results_layout.addWidget(self.results_list)
        splitter.addWidget(results_widget)

        # Mod detail view
        detail_widget = QWidget()
        detail_layout = QVBoxLayout(detail_widget)
        detail_layout.setContentsMargins(10, 0, 20, 20)
        
        self.mod_title = QLabel("Select a mod to see details")
        self.mod_title.setObjectName("title_label")
        self.mod_title.setWordWrap(True)
        detail_layout.addWidget(self.mod_title)
        
        self.mod_summary = QLabel()
        self.mod_summary.setWordWrap(True)
        detail_layout.addWidget(self.mod_summary)
        
        self.mod_description = QTextEdit()
        self.mod_description.setReadOnly(True)
        detail_layout.addWidget(self.mod_description, 1)
        
        download_layout = QHBoxLayout()
        self.version_combo = QComboBox()
        self.version_combo.setPlaceholderText("Select a version to download")
        download_layout.addWidget(self.version_combo, 1)
        
        self.download_button = QPushButton("Download")
        self.download_button.setEnabled(False)
        self.download_button.clicked.connect(self.start_download)
        download_layout.addWidget(self.download_button)
        detail_layout.addLayout(download_layout)
        
        self.download_status_label = QLabel("")
        self.download_status_label.setObjectName("status_label")
        detail_layout.addWidget(self.download_status_label)
        
        splitter.addWidget(detail_widget)
        
        splitter.setSizes([400, 300])

    @pyqtSlot()
    def start_search(self):
        query = self.search_input.text().strip()
        if not query:
            return

        self.search_button.setText("Searching...")
        self.search_button.setEnabled(False)
        
        game_versions = [self.game_version] if self.game_version else None
        
        # In a real app, this should be in a QThread
        self.search_results = self.modrinth_client.search(query, game_versions=game_versions, loader=self.loader)
        self.populate_results()
        
        self.search_button.setText("Search")
        self.search_button.setEnabled(True)

    def populate_results(self):
        self.results_list.clear()
        if not self.search_results:
            item = QListWidgetItem("No results found.")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.results_list.addItem(item)
            return
            
        for mod in self.search_results:
            item = QListWidgetItem(mod.get("title", "Unknown Mod"))
            item.setData(Qt.ItemDataRole.UserRole, mod)
            self.results_list.addItem(item)

    @pyqtSlot()
    def on_mod_selected(self):
        selected_items = self.results_list.selectedItems()
        if not selected_items:
            self.download_button.setEnabled(False)
            self.version_combo.clear()
            return

        mod_data = selected_items[0].data(Qt.ItemDataRole.UserRole)
        self.mod_title.setText(mod_data.get("title"))
        self.mod_summary.setText(mod_data.get("summary"))
        self.mod_description.setMarkdown(mod_data.get("description"))
        
        # Fetch and populate versions
        self.version_combo.clear()
        self.version_combo.setEnabled(False)
        self.version_combo.setPlaceholderText("Loading versions...")
        
        game_versions = [self.game_version] if self.game_version else None
        
        # This should also be in a thread
        versions = self.modrinth_client.get_versions(mod_data.get("project_id"), game_versions=game_versions, loader=self.loader)
        self.version_combo.setPlaceholderText("Select a version to download")
        self.version_combo.setEnabled(True)
        
        if not versions:
            self.version_combo.addItem("No compatible versions found")
            self.download_button.setEnabled(False)
            return
            
        for version in versions:
            # Find the first valid file
            valid_file = next((f for f in version.get("files", []) if f.get("url")), None)
            if valid_file:
                self.version_combo.addItem(version.get("name"), userData=valid_file)

        self.download_button.setEnabled(self.version_combo.count() > 0 and "No compatible" not in self.version_combo.itemText(0))

    @pyqtSlot()
    def start_download(self):
        selected_index = self.version_combo.currentIndex()
        if selected_index < 0:
            return
            
        file_data = self.version_combo.itemData(selected_index)
        if not file_data or not file_data.get("url"):
            self.download_status_label.setText("⚠️ Invalid download URL.")
            return

        url = file_data.get("url")
        
        self.download_button.setEnabled(False)
        self.download_button.setText("Downloading...")
        self.download_status_label.setText(f"Downloading {file_data.get('filename')}...")

        self.downloader_thread = QThread()
        self.downloader = ModDownloader(url)
        self.downloader.moveToThread(self.downloader_thread)

        self.downloader_thread.started.connect(self.downloader.run)
        self.downloader.finished.connect(self.on_download_finished)

        self.downloader.finished.connect(self.downloader_thread.quit)
        self.downloader.finished.connect(self.downloader.deleteLater)
        self.downloader_thread.finished.connect(self.downloader_thread.deleteLater)

        self.downloader_thread.start()

    @pyqtSlot(bool, str)
    def on_download_finished(self, success, message):
        self.download_button.setEnabled(True)
        self.download_button.setText("Download")
        self.download_status_label.setText(message)
        if success:
            # Could emit a signal to the main window to refresh the mods page
            pass
