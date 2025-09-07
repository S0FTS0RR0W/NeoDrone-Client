import requests
import hashlib
import random

class NavidromeAPI:
    def __init__(self, base_url, username, password):
        if not base_url.startswith("http://") and not base_url.startswith("https://"):
            base_url = "http://" + base_url
        self.base_url = base_url.rstrip("/") + "/rest"
        self.username = username
        self.password = password
        self.client_name = "ComfortClient"
        self.api_version = "1.16.1"
        self.salt = str(random.randint(1000, 9999))
        self.token = self._generate_token(password)

    def _generate_token(self, password):
        hash_input = password + self.salt
        return hashlib.md5(hash_input.encode()).hexdigest()

    def _build_params(self, extra=None):
        params = {
            "u": self.username,
            "t": self.token,
            "s": self.salt,
            "v": self.api_version,
            "c": self.client_name,
            "f": "json"
        }
        if extra:
            params.update(extra)
        return params

    def ping(self):
        url = f"{self.base_url}/ping.view"
        response = requests.get(url, params=self._build_params())
        return response.json()

    def get_artists(self):
        url = f"{self.base_url}/getArtists.view"
        response = requests.get(url, params=self._build_params())
        return response.json()

    def get_artist(self, artist_id):
        url = f"{self.base_url}/getArtist.view"
        params = self._build_params({"id": artist_id})
        response = requests.get(url, params=params)
        return response.json()

    def get_album(self, album_id):
        url = f"{self.base_url}/getAlbum.view"
        params = self._build_params({"id": album_id})
        response = requests.get(url, params=params)
        return response.json()