import os
import requests
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QThread

from .constants import ICON_CACHE_DIR

class ImageDownloader(QObject):
    finished = pyqtSignal(str, str)

    def __init__(self, url, cache_path):
        super().__init__()
        self.url = url
        self.cache_path = cache_path

    @pyqtSlot()
    def run(self):
        try:
            response = requests.get(self.url)
            response.raise_for_status()

            os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)

            with open(self.cache_path, "wb") as f:
                f.write(response.content)
            self.finished.emit(self.url, self.cache_path)
        except Exception as e:
            print(f"Error downloading image: {e}")
            self.finished.emit(self.url, "")

class ImageCache(QObject):
    image_downloaded = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.downloader_threads = []

    def get_image(self, url):
        filename = url.split("/")[-1]
        cache_path = os.path.join(ICON_CACHE_DIR, filename)

        if os.path.exists(cache_path):
            return cache_path
        else:
            self.download_image(url, cache_path)
            return None

    def download_image(self, url, cache_path):
        thread = QThread()
        downloader = ImageDownloader(url, cache_path)
        downloader.moveToThread(thread)

        thread.started.connect(downloader.run)
        downloader.finished.connect(self.on_image_downloaded)

        downloader.finished.connect(thread.quit)
        downloader.finished.connect(downloader.deleteLater)
        thread.finished.connect(thread.deleteLater)

        thread.start()
        self.downloader_threads.append(thread)

    @pyqtSlot(str, str)
    def on_image_downloaded(self, url, path):
        self.image_downloaded.emit(url, path)
