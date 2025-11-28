import os
import shutil
import json

from PyQt6.QtCore import pyqtSignal, QSize, Qt, QThread, pyqtSlot, QPropertyAnimation, QEasingCurve, QPointF, QEvent
from PyQt6.QtGui import QPixmap, QColor
from PyQt6.QtWidgets import (
    QListWidget,
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QDialog,
    QTextEdit,
    QTextBrowser,
    QGraphicsDropShadowEffect,
)

import markdown

from bs4 import BeautifulSoup

from .constants import MODS_DIR, ICON_CACHE_DIR
from .modrinth_client import ModrinthClient
from .workers import ModDownloader, ProjectFetcher
from .image_cache import ImageCache

class ModDetailDialog(QDialog):
    def __init__(self, mod_data, modrinth_client: ModrinthClient, parent=None):
        super().__init__(parent)
        self.mod_data = mod_data
        self.modrinth_client = modrinth_client
        self.fetcher_thread = None
        self.fetcher = None
        self.image_cache = ImageCache(self)
        self.image_cache.image_downloaded.connect(self.on_image_downloaded)
        self.html = ""

        self.setWindowTitle(self.mod_data.get("title", "Mod Details"))
        self.setMinimumSize(800, 600)

        self.init_ui()
        self.fetch_description()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        self.title_label = QLabel(self.mod_data.get("title"))
        self.title_label.setObjectName("title_label")
        layout.addWidget(self.title_label)

        self.summary_label = QLabel(self.mod_data.get("summary"))
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)

        self.details_browser = QTextBrowser()
        self.details_browser.setOpenExternalLinks(True)
        self.details_browser.setSearchPaths([ICON_CACHE_DIR])
        layout.addWidget(self.details_browser, 1)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

    def fetch_description(self):
        self.details_browser.setPlaceholderText("Loading description...")

        self.fetcher_thread = QThread()
        self.fetcher = ProjectFetcher(self.modrinth_client, self.mod_data.get("slug"))
        self.fetcher.moveToThread(self.fetcher_thread)

        self.fetcher_thread.started.connect(self.fetcher.run)
        self.fetcher.finished.connect(self.on_description_fetched)

        self.fetcher.finished.connect(self.fetcher_thread.quit)
        self.fetcher.finished.connect(self.fetcher.deleteLater)
        self.fetcher_thread.finished.connect(self.fetcher_thread.deleteLater)

        self.fetcher_thread.start()

    @pyqtSlot(dict)
    def on_description_fetched(self, project_data):
        if project_data and "body" in project_data:
            markdown_text = project_data["body"]
            self.html = markdown.markdown(markdown_text)
            self.details_browser.setHtml(self.html)
            self.process_images()
        else:
            self.details_browser.setPlaceholderText("Failed to load description.")

    def process_images(self):
        soup = BeautifulSoup(self.html, "lxml")
        for img in soup.find_all("img"):
            url = img.get("src")
            if url:
                cached_path = self.image_cache.get_image(url)
                if cached_path:
                    self.rewrite_image_path(url, cached_path)

    @pyqtSlot(str, str)
    def on_image_downloaded(self, url, path):
        self.rewrite_image_path(url, path)

    def rewrite_image_path(self, url, path):
        soup = BeautifulSoup(self.html, "lxml")
        img_tags = soup.find_all('img', src=url)
        for img in img_tags:
            img['src'] = f"file:///{os.path.abspath(path)}"
        self.html = str(soup)
        self.details_browser.setHtml(self.html)
        self.details_browser.reload()

class ModListItem(QWidget):
    card_clicked = pyqtSignal(dict)

    def __init__(self, mod_data, modrinth_client: ModrinthClient, game_version: str | None, loader: str | None, parent=None):
        super().__init__(parent)
        self.mod_data = mod_data
        self.modrinth_client = modrinth_client
        self.game_version = game_version
        self.loader = loader
        self.icon_path = None
        self.downloader_thread = None
        self.downloader = None

        self.init_ui()
        self.setup_animations()

    def init_ui(self):
        self.setObjectName("mod_card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        self.icon_label = QLabel()
        self.icon_label.setFixedSize(QSize(128, 128))
        self.icon_label.setStyleSheet("background-color: #333;") # Placeholder
        layout.addWidget(self.icon_label, 0, Qt.AlignmentFlag.AlignCenter)

        self.title_label = QLabel(self.mod_data.get("title", "Unknown Mod"))
        self.title_label.setObjectName("mod_card_title")
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label, 0, Qt.AlignmentFlag.AlignCenter)

        downloads_label = QLabel(f"Downloads: {self.mod_data.get('downloads', 0):,}")
        downloads_label.setObjectName("mod_card_downloads")
        layout.addWidget(downloads_label, 0, Qt.AlignmentFlag.AlignCenter)

        self.download_button = QPushButton("Download")
        self.download_button.setObjectName("download_badge")
        self.download_button.clicked.connect(self.start_download)
        layout.addWidget(self.download_button, 0, Qt.AlignmentFlag.AlignCenter)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0,0)
        layout.addWidget(self.progress_bar)

    def setup_animations(self):
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(10)
        self.shadow.setColor(QColor(0, 0, 0, 80))
        self.shadow.setOffset(0, 2)
        self.setGraphicsEffect(self.shadow)

        self.anim_blur = QPropertyAnimation(self.shadow, b"blurRadius")
        self.anim_blur.setDuration(200)
        self.anim_blur.setEasingCurve(QEasingCurve.Type.OutQuad)

        self.anim_offset = QPropertyAnimation(self.shadow, b"offset")
        self.anim_offset.setDuration(200)
        self.anim_offset.setEasingCurve(QEasingCurve.Type.OutQuad)

    def enterEvent(self, event):
        self.anim_blur.stop()
        self.anim_blur.setEndValue(25)
        self.anim_blur.start()

        self.anim_offset.stop()
        self.anim_offset.setEndValue(QPointF(0, 8))
        self.anim_offset.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.anim_blur.stop()
        self.anim_blur.setEndValue(10)
        self.anim_blur.start()

        self.anim_offset.stop()
        self.anim_offset.setEndValue(QPointF(0, 2))
        self.anim_offset.start()
        super().leaveEvent(event)

    def set_icon(self, icon_path):
        if icon_path:
            self.icon_path = icon_path
            pixmap = QPixmap(icon_path)
            self.icon_label.setPixmap(pixmap.scaled(128, 128, aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio))

    def mousePressEvent(self, event):
        if not self.download_button.underMouse():
            self.card_clicked.emit(self.mod_data)
        super().mousePressEvent(event)


    @pyqtSlot()
    def start_download(self):
        if not self.game_version or not self.loader:
            self.download_button.setText("Select version/loader")
            return

        self.download_button.setEnabled(False)
        self.download_button.setText("Getting info...")

        game_versions = [self.game_version] if self.game_version else None
        versions = self.modrinth_client.get_versions(self.mod_data.get("project_id"), game_versions=game_versions, loader=self.loader)

        if not versions:
            self.download_button.setText("No compatible versions")
            return

        latest_version = versions[0]
        valid_file = next((f for f in latest_version.get("files", []) if f.get("url")), None)

        if not valid_file or not valid_file.get("url"):
            self.download_button.setText("Download failed")
            return

        url = valid_file.get("url")

        self.download_button.setVisible(False)
        self.progress_bar.setVisible(True)

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
        self.progress_bar.setVisible(False)
        self.download_button.setVisible(True)
        self.download_button.setEnabled(True)
        if success:
            self.download_button.setText("Downloaded")
        else:
            self.download_button.setText("Error")



class ModListWidget(QListWidget):
    mods_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.DragDropMode.DropOnly)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile() and url.toLocalFile().endswith(".jar"):
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
                if file_path.endswith(".jar"):
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
