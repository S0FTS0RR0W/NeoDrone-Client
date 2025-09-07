from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QTabWidget, QHBoxLayout,
    QPushButton, QLineEdit, QMessageBox, QListWidget, QListWidgetItem, QFrame, QSlider
)
from PyQt6.QtGui import QFont, QPixmap, QIcon
from PyQt6.QtCore import Qt
from api import NavidromeAPI
from config import load_config, save_config
import vlc
import requests

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.config = load_config()

        self.setWindowTitle("Navidrome Comfort Client")
        self.resize(800, 600)
        self.setMinimumSize(600, 400)

        # Auto connect logic

        server = self.config.get("server")
        username = self.config.get("username")
        password = self.config.get("password")

        self.api = None
        if server and username and password:
            try:
                self.api = NavidromeAPI(server, username, password)
                ping = self.api.ping()
                if "subsonic-response" in ping:
                    print("✅ Auto-connected to Navidrome.")
                else:
                    print("⚠️ Ping failed. Manual login may be required.")
            except Exception as e:
                print(f"❌ Auto-connect error: {e}")


        self.offline_enabled = self.config.get("offline", False)
        self.affirmation_style = "Gentle"

        self.setup_ui()


    def setup_ui(self):
        # Enable UI Transparency
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")

        # Background image using QLabel
        bg_label = QLabel(self)
        bg_pixmap = QPixmap("assets/background.jpg")
        bg_label.setPixmap(bg_pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding))
        bg_label.setGeometry(0, 0, self.width(), self.height())
        bg_label.lower()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Library Tab
        library_tab = QWidget()
        library_layout = QVBoxLayout()
        library_tab.setLayout(library_layout)

        header = QLabel("✨ Explore your musical anchors")
        header.setFont(QFont("Arial", 16))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("color: white; padding: 10px;")
        library_layout.addWidget(header)

        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 0.5);
                border-radius: 12px;
                padding: 10px;
            }
        """)
        frame_layout = QVBoxLayout()
        frame.setLayout(frame_layout)

        self.artist_list = QListWidget()
        self.artist_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                font-size: 14px;
                color: white;
            }
            QListWidget::item {
                padding: 6px;
            }
            QListWidget::item:selected {
                background-color: #66aaff;
                color: white;
            }
        """)
        self.artist_list.itemClicked.connect(self.on_artist_selected)
        frame_layout.addWidget(self.artist_list)
        library_layout.addWidget(frame)

        refresh_button = QPushButton("Refresh Library")
        refresh_icon = QIcon("assets/icons/arrow-alt-circle-up.svg")
        refresh_button.setIcon(refresh_icon)
        refresh_button.setStyleSheet("padding: 8px; font-weight: bold;")
        refresh_button.clicked.connect(self.load_artists)
        library_layout.addWidget(refresh_button)

    # Play button
        play_button = QPushButton("Play First Track")
        play_icon = QIcon("assets/icons/circle-play.svg")
        play_button.setIcon(play_icon)
        play_button.setStyleSheet("padding: 8px; font-weight: bold;")
        play_button.clicked.connect(self.play_first_track)
        library_layout.addWidget(play_button)

        tabs.addTab(library_tab, "Library")

        # Now Playing Tab
        now_tab = QWidget()
        now_layout = QVBoxLayout()
        now_tab.setLayout(now_layout)

        self.now_label = QLabel("Now Playing: nothing.")
        self.now_label.setFont(QFont("Arial", 14))
        self.now_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.now_label.setStyleSheet("color: white; padding: 10px;")
        now_layout.addWidget(self.now_label)

        self.album_art_label = QLabel()
        self.album_art_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.album_art_label.setFixedSize(200, 200)
        self.album_art_label.setStyleSheet("border-radius: 12px; background-color: rgba(0,0,0,0.3);")
        now_layout.addWidget(self.album_art_label)

        # Seek bar
        self.seek_slider = QSlider(Qt.Orientation.Horizontal)
        self.seek_slider.setRange(0, 100)
        self.seek_slider.setValue(0)
        self.seek_slider.setStyleSheet("padding: 8px;")
        self.seek_slider.sliderMoved.connect(self.seek_position)
        now_layout.addWidget(self.seek_slider)

        controls = QHBoxLayout()

        prev_button = QPushButton()
        prev_icon = QIcon("assets/icons/circle-left.svg")
        prev_button.setIcon(prev_icon)
        prev_button.setToolTip("Previous track")
        prev_button.clicked.connect(self.play_previous_track)

        play_pause_button = QPushButton()
        play_pause_icon = QIcon("assets/icons/circle-play.svg")
        play_pause_button.setIcon(play_pause_icon)
        play_pause_button.setToolTip("Play / Pause")
        play_pause_button.clicked.connect(self.toggle_play_pause)

        next_button = QPushButton()
        next_icon = QIcon("assets/icons/circle-right.svg")
        next_button.setIcon(next_icon)
        next_button.setToolTip("Next track")
        next_button.clicked.connect(self.play_next_track)

        for btn in [prev_button, play_pause_button, next_button]:
            btn.setStyleSheet("padding: 8px; font-size: 16px; font-weight: bold;")

        controls.addWidget(prev_button)
        controls.addWidget(play_pause_button)
        controls.addWidget(next_button)
        now_layout.addLayout(controls)

        tabs.addTab(now_tab, "Now Playing")

        # Settings Tab
        settings_tab = QWidget()
        settings_layout = QVBoxLayout()
        settings_tab.setLayout(settings_layout)

        theme_label = QLabel("Theme Mode")
        theme_label.setFont(QFont("Arial", 14))
        settings_layout.addWidget(theme_label)

        theme_buttons = QHBoxLayout()
        for mode in ["Cozy", "Focused", "Ambient"]:
            btn = QPushButton(mode)
            btn.clicked.connect(lambda _, m=mode: self.apply_theme(m))
            theme_buttons.addWidget(btn)
        settings_layout.addLayout(theme_buttons)

        login_label = QLabel("Navidrome Login")
        login_label.setFont(QFont("Arial", 14))
        settings_layout.addWidget(login_label)

        self.server_input = QLineEdit()
        self.server_input.setPlaceholderText("Server URL (e.g. http://localhost:4533)")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.server_input.setText(self.config.get("server", ""))
        self.username_input.setText(self.config.get("username", ""))
        self.password_input.setText(self.config.get("password", ""))

        self.apply_theme(self.config.get("theme", "Cozy"))
        self.affirmation_style = self.config.get("affirmation_style", "Gentle")

        settings_layout.addWidget(self.server_input)
        settings_layout.addWidget(self.username_input)
        settings_layout.addWidget(self.password_input)

        connect_button = QPushButton("Connect to Navidrome")
        connect_button.clicked.connect(self.connect_to_navidrome)
        settings_layout.addWidget(connect_button)

        offline_label = QLabel("💾 Offline Mode")
        offline_label.setFont(QFont("Arial", 14))
        settings_layout.addWidget(offline_label)

        offline_toggle = QPushButton("Enable Offline Mode")
        offline_toggle.clicked.connect(self.toggle_offline_mode)
        settings_layout.addWidget(offline_toggle)

        affirm_label = QLabel("🧘 Affirmation Style")
        affirm_label.setFont(QFont("Arial", 14))
        settings_layout.addWidget(affirm_label)

        affirm_buttons = QHBoxLayout()
        for style in ["Gentle", "Playful", "Poetic"]:
            btn = QPushButton(style)
            btn.clicked.connect(lambda _, s=style: self.set_affirmation_style(s))
            affirm_buttons.addWidget(btn)
        settings_layout.addLayout(affirm_buttons)

        tabs.addTab(settings_tab, "Settings")

        # Auto refresh on start
        self.load_artists()
    # toggle offline mode

    def toggle_offline_mode(self):
        self.offline_enabled = not self.offline_enabled
        status = "enabled" if self.offline_enabled else "disabled"
        QMessageBox.information(self, "Offline Mode", f"Offline mode {status}.")
        self.config["offline"] = self.offline_enabled
        save_config(self.config)
    
    # New method to connect to Navidrome

    def connect_to_navidrome(self):
        server = self.server_input.text()
        username = self.username_input.text()
        password = self.password_input.text()

        if not server.startswith("http://") and not server.startswith("https://"):
            server = "http://" + server

        if not server or not username or not password:
            QMessageBox.warning(self, "Missing Info", "Please fill in all login fields.")
            return

        try:
            self.api = NavidromeAPI(server, username, password)
            ping = self.api.ping()
            if "subsonic-response" in ping:
                QMessageBox.information(self, "Connected", "🎉 Successfully connected to Navidrome!")
                self.config.update({
                    "server": server,
                    "username": username,
                    "password": password
                })
                save_config(self.config)
            else:
                QMessageBox.warning(self, "Connection Failed", "Could not connect. Check your details.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Something went wrong:\n{str(e)}")

    # New method to load artists

    def load_artists(self):
        if not self.api:
            QMessageBox.warning(self, "Not Connected", "Please connect to Navidrome first.")
            return

        try:
            data = self.api.get_artists()
            indexes = data.get("subsonic-response", {}).get("artists", {}).get("index", [])
            self.artist_list.clear()

            for group in indexes:
                for artist in group.get("artist", []):
                    name = artist.get("name", "Unknown Artist")
                    albums = artist.get("albumCount", 0)
                    display_text = f"{name}  •  {albums} album{'s' if albums != 1 else ''}"
                    item = QListWidgetItem(display_text)
                    item.setData(Qt.ItemDataRole.UserRole, artist)
                    self.artist_list.addItem(item)

            count = self.artist_list.count()
            #if count > 0:
                #QMessageBox.information(self, "Library Loaded", f"🎶 Loaded {count} artists.")
            #else:
                #QMessageBox.information(self, "Library Empty", "No artists found. Time to discover something new 🎧")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load artists:\n{str(e)}")

    def on_artist_selected(self, item):
        artist = item.data(Qt.ItemDataRole.UserRole)
        name = artist.get("name", "Unknown Artist")
        albums = artist.get("albumCount", 0)
        message = f"🎤 {name}\nAlbums available: {albums}\n\nFeeling inspired?"
        #QMessageBox.information(self, "Artist Selected", message)

    # Apply theme

    def apply_theme(self, mode):
        if mode == "Cozy":
            self.setStyleSheet("QMainWindow { background-color: #fbeec1; }")
        elif mode == "Focused":
            self.setStyleSheet("QMainWindow { background-color: #d0e6f6; }")
        elif mode == "Ambient":
            self.setStyleSheet("QMainWindow { background-color: #2e2e2e; color: white; }")

        self.config["theme"] = mode
        save_config(self.config)

    def set_affirmation_style(self, style):
        self.affirmation_style = style
        self.config["affirmation_style"] = style
        save_config(self.config)
        QMessageBox.information(self, "Affirmation Style", f"Affirmation style set to: {style}")

    def play_stream(self, track_id, cover_id=None):
        if not self.api:
            QMessageBox.warning(self, "Not Connected", "Connect to Navidrome first.")
            return
        
        # Fetch and display album art if cover_id is provided and valid
        if cover_id and isinstance(cover_id, str) and cover_id.strip():
            cover_url = f"{self.api.base_url}/coverArt.view?id={cover_id}&u={self.api.username}&t={self.api.token}&s={self.api.salt}&v={self.api.api_version}&c=ComfortClient"
            print(f"[DEBUG] Fetching album art from: {cover_url}")
            try:
                response = requests.get(cover_url)
                if response.status_code == 200 and response.content:
                    pixmap = QPixmap()
                    success = pixmap.loadFromData(response.content)
                    if success and not pixmap.isNull():
                        self.album_art_label.setPixmap(
                            pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        )
                    else:
                        print("⚠️ Pixmap is null or failed to load.")
                        self.album_art_label.setPixmap(QPixmap("assets/default_cover.png"))
                else:
                    print(f"❌ Failed to fetch image. Status: {response.status_code}")
                    self.album_art_label.setPixmap(QPixmap("assets/default_cover.png"))
            except Exception as e:
                print(f"❌ Exception while fetching album art: {e}")
                self.album_art_label.setPixmap(QPixmap("assets/default_cover.png"))
        else:
            print(f"[DEBUG] Invalid cover_id: {cover_id}")

        # Stop previous player if exists
        if hasattr(self, "player") and self.player:
            try:
                self.player.stop()
                self.player.release()
            except Exception:
                pass
        # If track_id is actually a dict (song object), extract info
        if isinstance(track_id, dict):
            song = track_id
        else:
            # fallback for legacy calls
            song = {"id": track_id, "title": f"Track {track_id}"}
        stream_url = f"{self.api.base_url}/stream.view?id={song['id']}&u={self.api.username}&t={self.api.token}&s={self.api.salt}&v={self.api.api_version}&c=ComfortClient"
        self.player = vlc.MediaPlayer(stream_url)
        self.player.play()
        song_title = song.get('title', f"Track {song['id']}")
        artist_name = song.get('artist', None)
        if not artist_name:
            # Try to get artist from album info if available
            if hasattr(self, 'current_album_tracks') and self.current_album_tracks:
                # Find the album's artist from the first track
                album_artist = self.current_album_tracks[0].get('artist', None)
                if album_artist:
                    artist_name = album_artist
        if artist_name:
            self.now_label.setText(f"▶️ Now Playing: {song_title} — {artist_name}")
        else:
            self.now_label.setText(f"▶️ Now Playing: {song_title}")

        # Store current track/album info for navigation
        self.current_track_id = song['id']
        self.current_cover_id = cover_id
        # If available, store album tracks for navigation
        if hasattr(self, "current_album_tracks") and self.current_album_tracks:
            for idx, t in enumerate(self.current_album_tracks):
                if t["id"] == song['id']:
                    self.current_track_index = idx
                    break
        # Start timer to update seek bar
        self.start_seek_timer()
    def start_seek_timer(self):
        # Use QTimer to update seek bar
        from PyQt6.QtCore import QTimer
        if hasattr(self, "seek_timer") and self.seek_timer:
            self.seek_timer.stop()
        self.seek_timer = QTimer(self)
        self.seek_timer.timeout.connect(self.update_seek_bar)
        self.seek_timer.start(500)

    def update_seek_bar(self):
        if hasattr(self, "player") and self.player:
            try:
                length = self.player.get_length()  # ms
                pos = self.player.get_time()  # ms
                if length > 0:
                    percent = int((pos / length) * 100)
                    self.seek_slider.setValue(percent)
            except Exception:
                pass

    def seek_position(self, value):
        if hasattr(self, "player") and self.player:
            length = self.player.get_length()
            if length > 0:
                seek_ms = int((value / 100) * length)
                self.player.set_time(seek_ms)

    # Get all artists

    def get_all_artists(self):
        if not self.api:
            QMessageBox.warning(self, "Not Connected", "Please connect to Navidrome first.")
            return []

        try:
            data = self.api.get_artists()
            indexes = data.get("subsonic-response", {}).get("artists", {}).get("index", [])
            artists = []
            for group in indexes:
                for artist in group.get("artist", []):
                    artists.append(artist)
            return artists
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load artists:\n{str(e)}")
            return []

        
    def get_album(self, album_id):
        if not self.api:
            QMessageBox.warning(self, "Not Connected", "Please connect to Navidrome first.")
            return None

        try:
            data = self.api.get_album(album_id)
            album = data.get("subsonic-response", {}).get("album", None)
            return album
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load album:\n{str(e)}")
            return None

    #Play first track

    def play_first_track(self):
        selected_item = self.artist_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "No Artist Selected", "Please select an artist first.")
            return

        artist = selected_item.data(Qt.ItemDataRole.UserRole)
        artist_id = artist.get("id")

        try:
            # Fetch artist data and albums
            artist_data = self.api.get_artist(artist_id)
            albums = artist_data.get("subsonic-response", {}).get("artist", {}).get("album", [])
            if not albums:
                QMessageBox.information(self, "No Albums", "This artist has no albums.")
                return

            # Get first album and its tracks
            first_album_id = albums[0]["id"]
            album_data = self.api.get_album(first_album_id)
            album_info = album_data.get("subsonic-response", {}).get("album", {})
            tracks = album_info.get("song", [])
            cover_id = album_info.get("coverArt")  # ✅ Defined here

            # Store album tracks for navigation
            self.current_album_tracks = tracks
            self.current_track_index = 0

            if not tracks:
                QMessageBox.information(self, "No Tracks", "This album has no tracks.")
                return

            # Play first track and pass cover_id
            self.play_stream(tracks[0], cover_id)
        except Exception as e:
            QMessageBox.critical(self, "Playback Error", f"Could not play track:\n{str(e)}")



    def toggle_play_pause(self):
        if hasattr(self, "player") and self.player:
            if self.player.is_playing():
                self.player.pause()
            else:
                self.player.play()

    def play_next_track(self):
        # Play next track in current album
        if hasattr(self, "current_album_tracks") and self.current_album_tracks:
            idx = getattr(self, "current_track_index", 0)
            if idx < len(self.current_album_tracks) - 1:
                next_track = self.current_album_tracks[idx + 1]
                self.current_track_index = idx + 1
                self.play_stream(next_track, self.current_cover_id)
            else:
                QMessageBox.information(self, "End of Album", "No more tracks in this album.")
        else:
            QMessageBox.information(self, "No Album", "No album loaded.")

    def play_previous_track(self):
        # Play previous track in current album
        if hasattr(self, "current_album_tracks") and self.current_album_tracks:
            idx = getattr(self, "current_track_index", 0)
            if idx > 0:
                prev_track = self.current_album_tracks[idx - 1]
                self.current_track_index = idx - 1
                self.play_stream(prev_track, self.current_cover_id)
            else:
                QMessageBox.information(self, "Start of Album", "Already at the first track.")
        else:
            QMessageBox.information(self, "No Album", "No album loaded.")