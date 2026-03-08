# This is a sample Python script with PySide6 UI.

from PySide6.QtWidgets import QApplication, QWidget
import sys


def main():
    app = QApplication(sys.argv)
    window = QWidget()
    window.setWindowTitle("FingerPunch")
    window.setGeometry(100, 100, 300, 200)
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
