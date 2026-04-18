import sys
from PySide6.QtWidgets import QApplication
from typingApp import TypingPracticeApp

def main():
    app = QApplication(sys.argv)
    window = TypingPracticeApp()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
