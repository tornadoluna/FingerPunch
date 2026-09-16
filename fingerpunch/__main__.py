import logging
import sys

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication

from fingerpunch.data_manager import StorageError
from fingerpunch.logging_config import (
    configure_logging,
    install_excepthook,
    log_file_path,
)
from fingerpunch.ui.main_window import TypingPracticeApp
from fingerpunch.ui.widgets import show_message

logger = logging.getLogger(__name__)


def main() -> None:
    configure_logging()
    install_excepthook()

    app = QApplication(sys.argv)
    QCoreApplication.setApplicationName("FingerPunch")

    logger.info("Starting FingerPunch")
    try:
        window = TypingPracticeApp()
    except StorageError as error:
        logger.critical("Could not open the database: %s", error)
        show_message(
            None,
            "FingerPunch could not start",
            f"The session database could not be opened.\n\n{error}\n\n"
            f"Details were written to {log_file_path()}",
        )
        sys.exit(1)

    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
