import sys
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QStyleFactory

from our_day.database.connection import initialize_database
from our_day.ui.main_window import MainWindow


def apply_light_theme(app: QApplication) -> None:
    app.setStyle(QStyleFactory.create("Fusion"))
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#F6F7FB"))
    palette.setColor(QPalette.WindowText, QColor("#222222"))
    palette.setColor(QPalette.Base, QColor("#FFFFFF"))
    palette.setColor(QPalette.AlternateBase, QColor("#F8F8FB"))
    palette.setColor(QPalette.Text, QColor("#222222"))
    palette.setColor(QPalette.Button, QColor("#FFFFFF"))
    palette.setColor(QPalette.ButtonText, QColor("#222222"))
    palette.setColor(QPalette.Highlight, QColor("#6B4EA0"))
    palette.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
    palette.setColor(QPalette.PlaceholderText, QColor("#9A9AA2"))
    app.setPalette(palette)


def main() -> None:
    initialize_database()
    app = QApplication(sys.argv)
    app.setApplicationName("Our Day")
    apply_light_theme(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
