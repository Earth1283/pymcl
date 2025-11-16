import json
import os
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional
import minecraft_launcher_lib
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from .constants import CLIENT_ID, REDIRECT_URL, MICROSOFT_INFO_PATH, MicrosoftInfo

class AuthHandler(BaseHTTPRequestHandler):
    def __init__(self, callback, *args, **kwargs):
        self.callback = callback
        super().__init__(*args, **kwargs)

    def do_GET(self):
        try:
            auth_code = self.path.split("?code=")[1]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"You can now close this window.")
            self.callback(auth_code)
        except IndexError:
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"Invalid request.")

class MicrosoftAuth(QObject):
    login_success = pyqtSignal(dict)
    login_failed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.server_thread = None
        self.http_server = None

    def start_login(self):
        login_url = minecraft_launcher_lib.microsoft_account.get_login_url(
            CLIENT_ID, REDIRECT_URL
        )
        webbrowser.open(login_url)

        self.server_thread = QThread()
        self.http_server = HTTPServer(("localhost", 8000), lambda *args, **kwargs: AuthHandler(self.finish_login, *args, **kwargs))
        self.server_thread.run = self.http_server.handle_request
        self.server_thread.start()

    def finish_login(self, auth_code):
        try:
            minecraft_info = minecraft_launcher_lib.microsoft_account.complete_login(
                CLIENT_ID,
                None,
                REDIRECT_URL,
                auth_code,
            )
            info: MicrosoftInfo = {
                "access_token": minecraft_info["access_token"],
                "refresh_token": minecraft_info["refresh_token"],
                "username": minecraft_info["username"],
                "uuid": minecraft_info["uuid"],
                "expires_in": minecraft_info["expires_in"],
                "login_time": int(time.time()),
            }
            self.save_microsoft_info(info)
            self.login_success.emit(info)
        except Exception as e:
            self.login_failed.emit(f"Login failed: {e}")
        finally:
            if self.http_server:
                self.http_server.server_close()
            if self.server_thread:
                self.server_thread.quit()
                self.server_thread.wait()

    def save_microsoft_info(self, info: MicrosoftInfo):
        with open(MICROSOFT_INFO_PATH, "w") as f:
            json.dump(info, f)

    def load_microsoft_info(self) -> Optional[MicrosoftInfo]:
        if os.path.exists(MICROSOFT_INFO_PATH):
            with open(MICROSOFT_INFO_PATH, "r") as f:
                return json.load(f)
        return None

    def refresh_token(self) -> Optional[MicrosoftInfo]:
        info = self.load_microsoft_info()
        if not info:
            return None

        try:
            new_info = minecraft_launcher_lib.microsoft_account.refresh_access_token(
                CLIENT_ID, None, info["refresh_token"], REDIRECT_URL
            )
            info: MicrosoftInfo = {
                "access_token": new_info["access_token"],
                "refresh_token": new_info["refresh_token"],
                "username": new_info["username"],
                "uuid": new_info["uuid"],
                "expires_in": new_info["expires_in"],
                "login_time": int(time.time()),
            }
            self.save_microsoft_info(info)
            return info
        except Exception:
            return None

    def is_token_expired(self) -> bool:
        info = self.load_microsoft_info()
        if not info:
            return True
        return int(time.time()) > info["login_time"] + info["expires_in"]
