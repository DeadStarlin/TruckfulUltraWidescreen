import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class InstallerTests(unittest.TestCase):
    def setUp(self):
        workspace = Path(__file__).resolve().parent
        self.temporary = tempfile.TemporaryDirectory(dir=workspace)
        assert Path(self.temporary.name).resolve().is_relative_to(workspace)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.mod = self.root / "mod"
        self.mod.mkdir()
        shutil.copy2(Path(__file__).with_name("install_border_files.py"), self.mod)
        (self.mod / "border-files").mkdir()
        (self.mod / "border-backup").mkdir()
        (self.root / "GameAssembly.dll").write_bytes(b"new original")
        (self.mod / "border-files/GameAssembly.dll").write_bytes(b"new patched")
        (self.mod / "border-backup/GameAssembly.dll").write_bytes(b"old original")
        entry = {"path": "GameAssembly.dll",
                 "original_sha256": hashlib.sha256(b"new original").hexdigest(),
                 "patched_sha256": hashlib.sha256(b"new patched").hexdigest()}
        (self.mod / "border-files/manifest.json").write_text(json.dumps([entry]))

    def run_installer(self, *arguments):
        return subprocess.run([sys.executable, str(self.mod / "install_border_files.py"), *arguments],
                              capture_output=True, text=True)

    def test_preserve_old_backup_install_and_restore(self):
        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stderr)
        archives = list((self.mod / "backup-archives").glob("border-*"))
        self.assertEqual(len(archives), 1)
        self.assertEqual((archives[0] / "GameAssembly.dll").read_bytes(), b"old original")
        self.assertEqual((self.mod / "border-backup/GameAssembly.dll").read_bytes(), b"new original")
        self.assertEqual((self.root / "GameAssembly.dll").read_bytes(), b"new patched")
        result = self.run_installer("--restore")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.root / "GameAssembly.dll").read_bytes(), b"new original")

    def test_unexpected_game_file_stops_before_archiving(self):
        (self.root / "GameAssembly.dll").write_bytes(b"unexpected edits")
        result = self.run_installer()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.mod / "backup-archives").exists())
        self.assertEqual((self.mod / "border-backup/GameAssembly.dll").read_bytes(), b"old original")
        self.assertEqual((self.root / "GameAssembly.dll").read_bytes(), b"unexpected edits")


if __name__ == "__main__":
    unittest.main()
