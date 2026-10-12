# TruckfulUltraWidescreen

Version **0.2 — borders removed and HUD at screen edges**. A reversible game-file patch for ultrawide Truckful gameplay. The default target is 3440×1440.

The patch expands the camera's maximum aspect ratio, disables separate side-panel images, and expands the gameplay HUD's shared layout. Existing anchors move the journal, speedometer, and other HUD elements toward the screen edges with their original sizes and margins. BepInEx is not required for these file edits.

## Tested game version

| Item | Tested value |
| --- | --- |
| Game | Truckful, Windows 64-bit |
| Steam App ID | 3090810 |
| Steam build ID | 25850103 |
| Unity engine | 6000.3.25f1 (e1dba0a9aba4) |
| Display | 3440×1440 |
| Verified | 12 October 2026 |

The Steam build ID identifies the tested game build; the Unity version identifies its engine. Other game builds are not verified. The camera constant's RVA (`0x2665F10`) is specific to this build.

## Install

Place this repository directly inside the Truckful installation directory. Start with original game files and close Truckful before installing. Use Python 3.10 or newer:

```powershell
cd TruckfulUltraWidescreen
python -m pip install -r requirements.txt
python prepare_borders.py
python install_border_files.py
python prepare_hud.py
python install_border_files.py --hud
```

Preparation creates patched copies and verifies that only the intended bytes changed. Installation verifies hashes, saves originals, and rolls back completed replacements if installation fails. Generated files and backups are excluded from Git.

The border patch changes the maximum-aspect constant in `GameAssembly.dll` and disables `Black_Left` / `Black_Right` Image components under `AreaController`. The HUD patch changes only the preferred width of `P_UI_Canvas_Gameplay/AreaController/Content`.

Choose the matching resolution in the game. For the default target, these Steam launch options request borderless 3440×1440:

```text
-screen-width 3440 -screen-height 1440 -screen-fullscreen 1 -window-mode borderless
```

## Different resolutions

Edit **resolution.py** before preparing files. Set `WIDTH` and `HEIGHT` to your display's target dimensions:

```python
WIDTH = 5120
HEIGHT = 1440
```

Both scripts use these values. The camera limit becomes `WIDTH / HEIGHT`; the HUD's preferred width becomes `1080 × WIDTH / HEIGHT`, because the game's HUD canvas scales against a reference height of 1080 UI units.

| Display resolution | Aspect ratio | HUD width in UI units |
| --- | --- | --- |
| 2560×1080 | 2.3704 | 2560 |
| 3440×1440 | 2.3889 | 2580 |
| 3840×1600 | 2.4000 | 2592 |
| 5120×1440 | 3.5556 | 3840 |

Only resolutions wider than 16:9 are accepted. If the patch is already installed, **restore the HUD first, then the borders**, edit resolution.py, and repeat the installation commands. Do not run preparation over already patched files. Update the game resolution and Steam launch options to match. Changing resolution.py alone does not alter installed game files.

The alternative resolutions above show the calculations; only 3440×1440 has been visually tested.

## Restore

Close Truckful and run from this repository:

```powershell
python install_border_files.py --hud --restore
python install_border_files.py --restore
```

Restore verifies current and backup hashes before replacement. Restore in that order because each step checks the expected scene-file hashes. Steam's Verify integrity also restores original files, but can invalidate these backups' expected installed hashes.

**Existing development installation:** its border patch was applied from the sibling `UltrawideMod` directory, while its HUD patch was applied from this repository. To restore that installation, use:

```powershell
python install_border_files.py --hud --restore
python ../UltrawideMod/install_border_files.py --restore
```

Keep backup directories until you have restored the corresponding changes.

## Validation and limits

The default border patch changed four bytes in `GameAssembly.dll` and disabled 161 image flags across 20 scene files. All 21 installed files passed SHA-256 verification. The HUD patch changed one preferred-width field per scene, from 1920 to 2580 UI units; all 20 scene files passed hash verification.

Gameplay was visually confirmed to have no side borders and correctly positioned HUD elements. Cutscenes and other resolutions remain untested. Game updates or Steam verification may overwrite the patch; check compatibility before reapplying it to a new build.

## License

The patch source is licensed under the [MIT License](LICENSE). Game files and generated backups are not included in this repository.
