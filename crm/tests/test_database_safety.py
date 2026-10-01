"""Regression checks for live SQLite backups and first-login credentials."""
import logging
import gc
import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

# data.py initializes a global manager at import. Keep that initialization away
# from the user's real AppData and avoid an open log handle during cleanup.
with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as app_dir, \
        patch.dict(os.environ, {"APPDATA": app_dir}), \
        patch("logging.FileHandler", return_value=logging.NullHandler()):
    from data import DatabaseManager
    gc.collect()


class DatabaseSafetyTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent)
        self.addCleanup(lambda: (gc.collect(), self.directory.cleanup()))
        self.root = Path(self.directory.name)
        self.manager = DatabaseManager.__new__(DatabaseManager)
        self.manager.logger = logging.getLogger(__name__)
        self.manager.db_path = str(self.root / "live.db")
        self.manager.get_app_data_dir = lambda: str(self.root)
        self.manager.initialize_database()

    def test_backup_includes_uncheckpointed_wal_data(self):
        with closing(sqlite3.connect(self.manager.db_path)) as writer:
            writer.execute("PRAGMA wal_autocheckpoint = 0")
            writer.execute("INSERT INTO ClinicInfo (clinic_name, clinic_address, license_number) VALUES (?, ?, ?)",
                           ("Test clinic", "Test address", "Test license"))
            writer.commit()
            self.assertTrue(os.path.exists(self.manager.db_path + "-wal"))

            target = self.root / "exports" / "snapshot.db"
            self.assertEqual(self.manager.backup_database(str(target)), str(target))
            with closing(sqlite3.connect(target)) as snapshot:
                self.assertEqual(snapshot.execute("SELECT clinic_name FROM ClinicInfo").fetchone()[0], "Test clinic")
                self.assertEqual(snapshot.execute("PRAGMA integrity_check").fetchone()[0], "ok")

    def test_backup_refuses_to_overwrite_live_database(self):
        self.assertIsNone(self.manager.backup_database(self.manager.db_path))
        with closing(sqlite3.connect(self.manager.db_path)) as connection:
            self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")

    def test_failed_backup_preserves_existing_snapshot(self):
        target = self.root / "saved.db"
        self.assertEqual(self.manager.backup_database(str(target)), str(target))
        original = target.read_bytes()
        with patch("data.sqlite3.connect", side_effect=sqlite3.OperationalError("source unavailable")):
            self.assertIsNone(self.manager.backup_database(str(target)))
        self.assertEqual(target.read_bytes(), original)
        self.assertEqual(list(self.root.glob(".clinic_backup_*.db")), [])

    def test_default_password_stays_blocked_until_changed(self):
        self.assertTrue(self.manager.must_change_password("doctor"))
        success, _ = self.manager.update_user_profile("doctor", {"password": "doctor123"})
        self.assertFalse(success)
        self.assertTrue(self.manager.must_change_password("doctor"))
        success, _ = self.manager.update_user_profile("doctor", {"password": "new-strong-password"})
        self.assertTrue(success)
        self.assertFalse(self.manager.must_change_password("doctor"))

    def test_migration_flags_published_default_password(self):
        legacy_path = self.root / "legacy.db"
        self.manager.db_path = str(legacy_path)
        with closing(sqlite3.connect(legacy_path)) as connection:
            connection.execute("CREATE TABLE Users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT, salt TEXT)")
            salt = "legacy-salt"
            connection.execute("INSERT INTO Users (username, password_hash, salt) VALUES (?, ?, ?)",
                               ("doctor", self.manager.hash_password("doctor123", salt), salt))
            connection.commit()
        self.manager.initialize_database()
        self.assertTrue(self.manager.must_change_password("doctor"))


if __name__ == "__main__":
    unittest.main()
