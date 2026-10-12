"""Install or restore the prepared border files, with hash checks and rollback."""
import hashlib
import json
import shutil
import sys
from pathlib import Path

MOD = Path(__file__).resolve().parent
ROOT = MOD.parent
STAGE = MOD / "border-files"
BACKUP = MOD / "border-backup"
restore = sys.argv[1:] == ["--restore"]
assert not sys.argv[1:] or restore, "Only --restore is supported."
entries = json.loads((STAGE / "manifest.json").read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace(source, target):
    temporary = target.with_name(target.name + ".truckful-ultrawide-tmp")
    assert not temporary.exists(), f"Unexpected temporary file: {temporary}"
    try:
        shutil.copy2(source, temporary)
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)


for entry in entries:
    target = (ROOT / entry["path"]).resolve()
    assert target.is_relative_to(ROOT) and (target.name == "GameAssembly.dll"
        or target.parent == ROOT / "Truckful_Data" and target.name.startswith("level")
        and target.name[5:].isdigit()), "Unexpected target path."
    source = (BACKUP if restore else STAGE) / entry["path"]
    expected = entry["original_sha256"] if restore else entry["patched_sha256"]
    assert digest(source) == expected, f"Prepared/backup file mismatch: {source}"
    assert digest(target) == entry["patched_sha256" if restore else "original_sha256"], \
        f"Game file changed since preparation: {target}; refusing to overwrite."

if not restore:
    for entry in entries:
        original = ROOT / entry["path"]
        backup = BACKUP / entry["path"]
        backup.parent.mkdir(parents=True, exist_ok=True)
        if not backup.exists():
            shutil.copy2(original, backup)
        assert digest(backup) == entry["original_sha256"], f"Backup mismatch: {backup}"

completed = []
try:
    for entry in entries:
        replace((BACKUP if restore else STAGE) / entry["path"], ROOT / entry["path"])
        completed.append(entry)
        expected = entry["original_sha256"] if restore else entry["patched_sha256"]
        assert digest(ROOT / entry["path"]) == expected
except BaseException:
    for entry in reversed(completed):
        replace((STAGE if restore else BACKUP) / entry["path"], ROOT / entry["path"])
    raise
print(f"{'Restored' if restore else 'Installed'} and verified {len(completed)} files.")
