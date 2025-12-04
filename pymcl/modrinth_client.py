import requests
import json

class ModrinthClient:
    BASE_URL = "https://api.modrinth.com/v2"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "PyMCL/1.0 (github.com/sonnynomnom/PyMCL)"}
        )

    def search(self, query, game_versions=None, loader=None, limit=20):
        params = {"query": query, "limit": limit}
        facets = []
        if game_versions:
            facets.append([f"versions:{v}" for v in game_versions])
        if loader:
            # Modrinth uses 'categories' for loaders in facets
            facets.append([f"categories:{loader}"])

        if facets:
            params["facets"] = json.dumps(facets)

        try:
            response = self.session.get(f"{self.BASE_URL}/search", params=params, timeout=15)
            response.raise_for_status()
            return response.json().get("hits", [])
        except requests.RequestException as e:
            print(f"Error searching Modrinth: {e}")
            return []

    def get_project(self, slug):
        try:
            response = self.session.get(f"{self.BASE_URL}/project/{slug}", timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error getting project from Modrinth: {e}")
            return {}

    def get_updates(self, file_hashes):
        print(f"ModrinthClient: Attempting to get updates for {len(file_hashes)} hashes.")
        try:
            response = self.session.post(
                f"{self.BASE_URL}/version_files/update",
                json={"hashes": file_hashes, "algorithm": "sha1"},
                timeout=15
            )
            response.raise_for_status()
            print("ModrinthClient: Successfully received update response.")
            return response.json()
        except requests.RequestException as e:
            print(f"ModrinthClient: Error getting updates: {e}")
            return {}

    def get_versions(self, mod_id, game_versions=None, loader=None):
        params = {}
        if game_versions:
            params["game_versions"] = json.dumps(game_versions)
        if loader:
            params["loaders"] = json.dumps([loader])

        try:
            response = self.session.get(f"{self.BASE_URL}/project/{mod_id}/version", params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error getting versions from Modrinth: {e}")
            return []
