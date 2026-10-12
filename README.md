# TruckfulUltraWidescreen

Version **0.1 — borders removed** enables border-free gameplay at 3440×1440.

The patch changes the game's maximum camera aspect ratio from 16:9 to 3440/1440 and disables the separate `Black_Left` / `Black_Right` UI images under `AreaController`. HUD layout and element sizes stay as shipped. This is a game-file patch; it does not require the abandoned ultrawide BepInEx plugin.

## Apply

Place this repository directly inside the Truckful installation directory. Start with original game files and close the game before installation. Use Python 3.10 or newer:

```powershell
cd TruckfulUltraWidescreen
python -m pip install -r requirements.txt
python prepare_borders.py
python install_border_files.py
```

Preparation writes patched copies to `border-files` and checks that only the intended bytes changed. Installation checks hashes, saves originals to `border-backup`, and rolls back completed replacements if installation fails. Generated game files and backups are excluded from Git.

## Restore

Close the game, then run from this repository:

```powershell
python install_border_files.py --restore
```

Restore verifies backup and current-file hashes before replacement. Steam's Verify integrity also restores original game files.

The existing development installation was applied from the sibling `UltrawideMod` directory. Its backups remain there; restore that installation with `python ../UltrawideMod/install_border_files.py --restore` before applying from this repository.

## Validation and limits

Tested on Truckful's Unity 6000.3.25f1 build with a 3440×1440 display. The installed patch changed four bytes in `GameAssembly.dll` and disabled 161 image flags across 20 scene files. All 21 installed files passed SHA-256 verification, and gameplay was visually confirmed to have no side borders.

The aspect constant's RVA is specific to this game build. Preparation refuses an unexpected constant. Game updates or Steam verification can overwrite the patch; recheck compatibility before applying it to another build. Cutscenes and other resolutions remain untested.
