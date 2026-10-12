"""Prepare byte-checked border edits; installation is a separate step."""
import hashlib
import json
import math
import struct
from pathlib import Path

MOD = Path(__file__).resolve().parent
ROOT = MOD.parent
import UnityPy
from resolution import ASPECT
from aspect_limit import find_aspect_offset

STAGE = MOD / "border-files"
STAGE.mkdir(exist_ok=True)
manifest = []


def stage(relative, original, changes):
    edited = bytearray(original)
    for offset, replacement in changes.items():
        edited[offset:offset + len(replacement)] = replacement
    expected = {offset + i for offset, data in changes.items()
                for i, value in enumerate(data) if original[offset + i] != value}
    actual = {i for i, (before, after) in enumerate(zip(original, edited)) if before != after}
    assert len(original) == len(edited) and actual == expected and actual
    target = STAGE / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(edited)
    manifest.append({"path": relative, "original_sha256": hashlib.sha256(original).hexdigest(),
                     "patched_sha256": hashlib.sha256(edited).hexdigest(),
                     "changed_bytes": len(actual)})
    print(f"Prepared {relative}: {len(actual)} changed bytes", flush=True)


binary = (ROOT / "GameAssembly.dll").read_bytes()
aspect_offset = find_aspect_offset(binary)
print(f"Located camera aspect limit at file offset 0x{aspect_offset:X}.", flush=True)
assert math.isclose(struct.unpack_from("<f", binary, aspect_offset)[0], 16 / 9, rel_tol=1e-7), \
    "Unexpected game build or an existing aspect patch; refusing to edit."
stage("GameAssembly.dll", binary, {aspect_offset: struct.pack("<f", ASPECT)})

total_images = 0
for path in sorted((ROOT / "Truckful_Data").glob("level*")):
    if not path.name[5:].isdigit():
        continue
    original = path.read_bytes()
    environment = UnityPy.load(str(path))
    changes = {}
    for obj in environment.objects:
        if obj.type.name != "GameObject":
            continue
        game_object = obj.read()
        if game_object.m_Name not in ("Black_Left", "Black_Right"):
            continue
        transform = game_object.m_Component[0].component.read()
        if not transform.m_Father.path_id or transform.m_Father.read().m_GameObject.read().m_Name != "AreaController":
            continue
        for component in game_object.m_Component:
            reader = component.component.deref()
            if reader.type.name != "MonoBehaviour" or reader.assets_file.name != path.name:
                continue
            behaviour = reader.read(check_read=False)
            if behaviour.m_Script.read().m_ClassName != "Image" or not behaviour.m_Enabled:
                continue
            raw = reader.get_raw_data()
            assert original[reader.byte_start:reader.byte_start + reader.byte_size] == raw
            assert raw[12] == 1  # Serialized MonoBehaviour.m_Enabled; retain its layout component.
            changes[reader.byte_start + 12] = b"\0"
    if changes:
        stage(str(path.relative_to(ROOT)), original, changes)
        total_images += len(changes)
assert total_images > 0, "No matching side images found; refusing an incomplete patch."
(STAGE / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(f"Ready: {total_images} side images across {len(manifest) - 1} scene files.", flush=True)
