import sys

from PySide6.QtWidgets import QApplication

from fingerpunch.ui.main_window import TypingPracticeApp


def main() -> None:
    app = QApplication(sys.argv)
    window = TypingPracticeApp()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
