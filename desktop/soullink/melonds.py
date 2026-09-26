from __future__ import annotations

import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Mapping


QT_KEYS = {
    "RETURN": 0x01000004,
    "ENTER": 0x01000005,
    "TAB": 0x01000001,
    "BACKSPACE": 0x01000003,
    "SHIFT": 0x01000020,
    "SPACE": 0x20,
    "LEFT": 0x01000012,
    "UP": 0x01000013,
    "RIGHT": 0x01000014,
    "DOWN": 0x01000015,
    "F11": 0x0100003A,
}

DEFAULT_KEYS = {
    "A": "X", "B": "Z", "X": "S", "Y": "A",
    "L": "Q", "R": "W", "Select": "SHIFT", "Start": "RETURN",
    "Up": "UP", "Down": "DOWN", "Left": "LEFT", "Right": "RIGHT",
    "HK_FastForward": "TAB", "HK_FullscreenToggle": "F11",
}


def qt_key(value: str) -> int:
    value = value.strip().upper()
    if value in QT_KEYS:
        return QT_KEYS[value]
    if len(value) == 1:
        return ord(value)
    raise ValueError(f"Unbekannte Taste: {value}")


def find_executable(selected: str | Path) -> Path:
    path = Path(selected).expanduser().resolve()
    if platform.system() == "Darwin" and path.suffix == ".app":
        path = path / "Contents" / "MacOS" / "melonDS"
    if not path.is_file():
        raise FileNotFoundError("melonDS wurde an diesem Ort nicht gefunden.")
    return path


def portable_directory(executable: Path) -> Path:
    if platform.system() == "Darwin" and executable.parent.name == "MacOS":
        return executable.parents[3] / "portable"
    return executable.parent / "portable"


def write_config(
    executable: Path,
    *,
    scale: int,
    fps: int,
    volume_percent: int,
    keys: Mapping[str, str],
    save_directory: Path,
) -> Path:
    if not 1 <= scale <= 16:
        raise ValueError("Die Auflösung muss zwischen 1× und 16× liegen.")
    if fps not in (60, 90, 120, 0):
        raise ValueError("FPS muss 60, 90, 120 oder unbegrenzt sein.")
    volume = round(max(0, min(100, volume_percent)) * 256 / 100)
    portable = portable_directory(executable)
    portable.mkdir(parents=True, exist_ok=True)
    save_directory.mkdir(parents=True, exist_ok=True)
    all_keys = {**DEFAULT_KEYS, **keys}
    values = {name: qt_key(value) for name, value in all_keys.items()}

    # A complete, deterministic portable profile avoids changing the user's
    # normal melonDS configuration and behaves identically on Windows/macOS.
    config = f'''PauseLostFocus = true
AudioSync = {str(fps == 60).lower()}
FastForwardFPS = 1000.0
LimitFPS = {str(fps != 0).lower()}
SlowmoFPS = 30.0
TargetFPS = {float(fps or 60):.1f}
UITheme = ""

[Audio]
Interpolation = 2
BitDepth = 0

[3D]
Renderer = 1

[3D.GL]
ScaleFactor = {scale}
BetterPolygons = true
HiresCoordinates = true

[Screen]
UseGL = true
Filter = true
VSync = {str(fps == 60).lower()}
VSyncInterval = 1

[Emu]
DirectBoot = true
ExternalBIOSEnable = false
ConsoleType = 0

[JIT]
Enable = true
MaxBlockSize = 32
BranchOptimisations = true
LiteralOptimisations = true
FastMemory = false

[Instance0]
SaveFilePath = "{_toml_path(save_directory)}"
SavestatePath = "{_toml_path(save_directory / 'states')}"
CheatFilePath = ""
EnableCheats = false
JoystickID = 0

[Instance0.Audio]
DSiVolumeSync = false
Volume = {volume}

[Instance0.Window0]
Enabled = true
ShowOSD = true
ScreenAspectTop = 0
ScreenAspectBot = 0
IntegerScaling = false
ScreenSizing = 0
ScreenLayout = 0
ScreenGap = 0
ScreenSwap = false
ScreenRotation = 0

[Instance0.Keyboard]
A = {values['A']}
B = {values['B']}
X = {values['X']}
Y = {values['Y']}
L = {values['L']}
R = {values['R']}
Select = {values['Select']}
Start = {values['Start']}
Up = {values['Up']}
Down = {values['Down']}
Left = {values['Left']}
Right = {values['Right']}
HK_FastForward = {values['HK_FastForward']}
HK_FullscreenToggle = {values['HK_FullscreenToggle']}
'''
    destination = portable / "melonDS.toml"
    destination.write_text(config, encoding="utf-8")
    return destination


def _toml_path(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/").replace('"', '\\"')


def launch(executable: Path, rom: Path, *, fullscreen: bool = True) -> subprocess.Popen:
    if not rom.is_file():
        raise FileNotFoundError("Die ausgewählte ROM wurde nicht gefunden.")
    command = [str(executable)]
    if fullscreen:
        command.append("--fullscreen")
    command.append(str(rom))
    return subprocess.Popen(command, cwd=str(executable.parent))


def copy_emulator(source: Path, destination: Path) -> Path:
    """Optional helper for making an isolated portable emulator copy."""
    if platform.system() == 'Darwin' and source.parent.name == 'MacOS' and source.parents[1].name == 'Contents':
        source = source.parents[2]
    if platform.system() == "Darwin" and source.suffix == ".app":
        target = destination / source.name
        if not target.exists():
            shutil.copytree(source, target)
        return target / "Contents" / "MacOS" / "melonDS"
    destination.mkdir(parents=True, exist_ok=True)
    # Qt DLLs/platform plugins beside the Windows executable are required too.
    shutil.copytree(source.parent, destination, dirs_exist_ok=True, ignore=shutil.ignore_patterns('portable'))
    target = destination / source.name
    return target
