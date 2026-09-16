import logging
import sys

import pytest

from fingerpunch import logging_config


@pytest.fixture
def isolated_logger(tmp_path, monkeypatch):
    monkeypatch.setattr(logging_config, "app_data_dir", lambda: tmp_path / "data")
    logger = logging.getLogger(logging_config.LOGGER_NAME)
    original = list(logger.handlers)
    original_level = logger.level
    logger.handlers = []
    yield logger
    for handler in logger.handlers:
        handler.close()
    logger.handlers = original
    logger.setLevel(original_level)


class TestConfigureLogging:
    def test_it_attaches_a_stream_and_a_file_handler(self, isolated_logger):
        logging_config.configure_logging()

        kinds = {type(handler).__name__ for handler in isolated_logger.handlers}
        assert "StreamHandler" in kinds
        assert "RotatingFileHandler" in kinds

    def test_calling_it_twice_does_not_duplicate_handlers(self, isolated_logger):
        logging_config.configure_logging()
        count = len(isolated_logger.handlers)

        logging_config.configure_logging()

        assert len(isolated_logger.handlers) == count

    def test_messages_reach_the_log_file(self, isolated_logger, tmp_path):
        logging_config.configure_logging()

        logging.getLogger("fingerpunch.test").info("a recorded message")
        for handler in isolated_logger.handlers:
            handler.flush()

        assert "a recorded message" in logging_config.log_file_path().read_text()

    def test_the_log_file_sits_beside_the_database(self, isolated_logger, tmp_path):
        assert logging_config.log_file_path().parent == tmp_path / "data"
        assert logging_config.log_file_path().name == logging_config.LOG_FILENAME

    def test_an_unwritable_directory_does_not_stop_the_app(self, isolated_logger, tmp_path, monkeypatch):
        blocked = tmp_path / "blocked"
        blocked.mkdir()
        blocked.chmod(0o500)
        monkeypatch.setattr(logging_config, "app_data_dir", lambda: blocked / "sub")

        logging_config.configure_logging()

        kinds = {type(handler).__name__ for handler in isolated_logger.handlers}
        assert "StreamHandler" in kinds
        assert "RotatingFileHandler" not in kinds
        blocked.chmod(0o700)

    def test_the_file_handler_rotates_rather_than_growing_without_limit(self, isolated_logger):
        logging_config.configure_logging()

        rotating = next(
            h for h in isolated_logger.handlers if type(h).__name__ == "RotatingFileHandler"
        )
        assert rotating.maxBytes == logging_config.MAX_LOG_BYTES
        assert rotating.backupCount == logging_config.BACKUP_COUNT


class TestExceptHook:
    def test_it_logs_the_exception_and_calls_the_previous_hook(self, isolated_logger, monkeypatch):
        logging_config.configure_logging()
        seen = []
        monkeypatch.setattr(sys, "excepthook", lambda *args: seen.append(args))
        records = []
        isolated_logger.addHandler(_Collector(records))

        logging_config.install_excepthook()
        error = ValueError("boom")
        sys.excepthook(ValueError, error, None)

        assert len(seen) == 1
        assert any(record.levelno == logging.CRITICAL for record in records)
        assert any("Unhandled exception" in record.getMessage() for record in records)

    def test_it_preserves_the_hook_it_replaced(self, isolated_logger, monkeypatch):
        sentinel = object()
        monkeypatch.setattr(sys, "excepthook", sentinel)

        logging_config.install_excepthook()

        assert sys.excepthook is not sentinel


class _Collector(logging.Handler):
    def __init__(self, records):
        super().__init__()
        self.records = records

    def emit(self, record):
        self.records.append(record)
