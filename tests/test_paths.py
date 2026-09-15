import sqlite3

import pytest
from PySide6.QtCore import QStandardPaths

from fingerpunch import paths
from fingerpunch.data_manager import DataManager


class TestAppDataDir:
    def test_the_app_directory_sits_under_the_platform_data_location(self, tmp_path, monkeypatch):
        monkeypatch.setattr(QStandardPaths, "writableLocation", lambda location: str(tmp_path))

        assert paths.app_data_dir() == tmp_path / paths.APP_DIRECTORY_NAME

    def test_an_empty_platform_location_falls_back_to_the_home_directory(self, monkeypatch, tmp_path):
        monkeypatch.setattr(QStandardPaths, "writableLocation", lambda location: "")
        monkeypatch.setattr(paths.Path, "home", staticmethod(lambda: tmp_path))

        assert paths.app_data_dir() == tmp_path / ".local" / "share" / paths.APP_DIRECTORY_NAME

    def test_the_database_lives_inside_the_app_directory(self, tmp_path, monkeypatch):
        monkeypatch.setattr(QStandardPaths, "writableLocation", lambda location: str(tmp_path))

        assert paths.default_database_path().parent == paths.app_data_dir()
        assert paths.default_database_path().name == paths.DATABASE_FILENAME

    def test_asking_for_the_path_does_not_create_anything(self, tmp_path, monkeypatch):
        monkeypatch.setattr(QStandardPaths, "writableLocation", lambda location: str(tmp_path))

        paths.default_database_path()

        assert list(tmp_path.iterdir()) == []


class TestDatabaseLocation:
    def test_the_default_database_does_not_follow_the_working_directory(self, tmp_path, monkeypatch):
        from fingerpunch import data_manager

        fixed = tmp_path / "data" / "typingStats.db"
        monkeypatch.setattr(data_manager, "default_database_path", lambda: fixed)

        monkeypatch.chdir(tmp_path)
        first = DataManager()
        (tmp_path / "elsewhere").mkdir()
        monkeypatch.chdir(tmp_path / "elsewhere")
        second = DataManager()

        assert first.db_path == second.db_path == str(fixed)

    def test_no_database_is_left_in_the_working_directory(self, tmp_path, monkeypatch):
        from fingerpunch import data_manager

        monkeypatch.setattr(data_manager, "default_database_path", lambda: tmp_path / "data" / "db.sqlite")
        work = tmp_path / "work"
        work.mkdir()
        monkeypatch.chdir(work)

        DataManager()

        assert list(work.iterdir()) == []

    def test_a_missing_parent_directory_is_created(self, tmp_path):
        target = tmp_path / "deeply" / "nested" / "typingStats.db"

        db = DataManager(str(target))

        assert target.exists()
        assert db.get_all_sessions() == []

    def test_an_explicit_path_is_honoured(self, tmp_path):
        target = tmp_path / "chosen.db"

        assert DataManager(str(target)).db_path == str(target)

    def test_a_path_object_is_accepted(self, tmp_path):
        target = tmp_path / "chosen.db"

        db = DataManager(target)

        assert db.db_path == str(target)
        with sqlite3.connect(db.db_path) as conn:
            assert conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 0


@pytest.fixture(autouse=True)
def _never_touch_the_real_data_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(QStandardPaths, "writableLocation", lambda location: str(tmp_path / "platform"))
