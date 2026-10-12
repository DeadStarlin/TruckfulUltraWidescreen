"""Expand only the gameplay HUD's preferred width; retain all existing border edits."""
import hashlib
import json
import struct
from pathlib import Path

import UnityPy
from resolution import ASPECT

MOD = Path(__file__).resolve().parent
ROOT = MOD.parent
STAGE = MOD / "hud-files"
STAGE.mkdir(exist_ok=True)
manifest = []
hud_width = struct.unpack("<f", struct.pack("<f", 1080 * ASPECT))[0]

for path in sorted((ROOT / "Truckful_Data").glob("level*")):
    if not path.name[5:].isdigit():
        continue
    original = path.read_bytes()
    edited = bytearray(original)
    environment = UnityPy.load(str(path))
    offsets = []
    for obj in environment.objects:
        if obj.type.name != "GameObject":
            continue
        content = obj.read()
        if content.m_Name != "Content":
            continue
        transform = content.m_Component[0].component.read()
        if not transform.m_Father.path_id:
            continue
        area = transform.m_Father.read()
        if area.m_GameObject.read().m_Name != "AreaController" or not area.m_Father.path_id:
            continue
        canvas = area.m_Father.read().m_GameObject.read()
        if canvas.m_Name != "P_UI_Canvas_Gameplay":
            continue
        scaler_checked = False
        for component in canvas.m_Component:
            reader = component.component.deref()
            if reader.type.name != "MonoBehaviour":
                continue
            behaviour = reader.read(check_read=False)
            if behaviour.m_Script.read().m_ClassName != "CanvasScaler":
                continue
            raw = reader.get_raw_data()
            assert struct.unpack_from("<i", raw, 32)[0] == 1
            assert struct.unpack_from("<ff", raw, 44) == (1920, 1080)
            assert struct.unpack_from("<f", raw, 56)[0] == 1
            scaler_checked = True
        assert scaler_checked, f"Unexpected HUD scaling in {path.name}."
        for component in content.m_Component:
            reader = component.component.deref()
            if reader.type.name != "MonoBehaviour":
                continue
            behaviour = reader.read(check_read=False)
            if behaviour.m_Script.read().m_ClassName != "LayoutElement":
                continue
            assert reader.assets_file.name == path.name
            raw = reader.get_raw_data()
            assert original[reader.byte_start:reader.byte_start + reader.byte_size] == raw
            assert struct.unpack_from("<f", raw, 44)[0] == 1920, "HUD width already changed."
            offset = reader.byte_start + 44  # LayoutElement.m_PreferredWidth.
            edited[offset:offset + 4] = struct.pack("<f", hud_width)
            assert struct.unpack_from("<f", edited, offset)[0] == hud_width
            offsets.append(offset)
    if not offsets:
        continue
    allowed = {offset + i for offset in offsets for i in range(4)}
    actual = {i for i, (before, after) in enumerate(zip(original, edited)) if before != after}
    assert len(original) == len(edited) and actual and actual.issubset(allowed)
    relative = str(path.relative_to(ROOT))
    target = STAGE / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(edited)
    manifest.append({"path": relative, "original_sha256": hashlib.sha256(original).hexdigest(),
                     "patched_sha256": hashlib.sha256(edited).hexdigest(), "changed_bytes": len(actual)})
    print(f"Prepared {relative}: {len(offsets)} HUD container(s), {len(actual)} changed bytes", flush=True)
assert manifest, "No gameplay HUD layouts found."
(STAGE / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(f"Ready: gameplay HUD width 1920 -> {hud_width:g} across {len(manifest)} scenes.", flush=True)
