# main.py

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from ui_main import MainWindow
import sys
from api import NavidromeAPI

api = NavidromeAPI("http://10.20.0.24:4533", "S0FTS0RR0W", "Gamerguy43")

def main():
    app = QApplication(sys.argv)

    # Optional: Set app icon and name
    app.setApplicationName("Navidrome Comfort Client")
    app.setWindowIcon(QIcon("assets/icon.png"))  # Add your icon later

    # Initialize main window
    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
