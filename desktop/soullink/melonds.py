from __future__ import annotations

import os
import platform
import shutil
import subprocess
import hashlib
import tomllib
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
    if value.startswith('QT:') and value[3:].lstrip('-').isdigit() and -(1<<31)<=int(value[3:])<(1<<31):
        return int(value[3:])
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
    pixel_filter: bool = False,
    integer_scaling: bool = False,
    screen_layout: str = 'focus',
    pause_lost_focus: bool = True,
    input_profile: dict | None = None,
) -> Path:
    if not 1 <= scale <= 16:
        raise ValueError("Die Auflösung muss zwischen 1× und 16× liegen.")
    if fps not in (60, 90, 120, 0):
        raise ValueError("FPS muss 60, 90, 120 oder unbegrenzt sein.")
    if screen_layout not in ('focus','horizontal','vertical'):
        raise ValueError('Unbekanntes Bildschirmlayout.')
    volume = round(max(0, min(100, volume_percent)) * 256 / 100)
    portable = portable_directory(executable)
    portable.mkdir(parents=True, exist_ok=True)
    save_directory.mkdir(parents=True, exist_ok=True)
    all_keys = {**DEFAULT_KEYS, **keys}
    values = {name: qt_key(value) for name, value in all_keys.items()}
    from .controls import validated
    profile=validated(input_profile or {})
    values={**profile['Keyboard'],**values}

    # A complete, deterministic portable profile avoids changing the user's
    # normal melonDS configuration and behaves identically on Windows/macOS.
    config = f'''PauseLostFocus = {str(pause_lost_focus).lower()}
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
Filter = {str(pixel_filter).lower()}
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
JoystickID = {profile['JoystickID']}

[Instance0.Audio]
DSiVolumeSync = false
Volume = {volume}

[Instance0.Window0]
Enabled = true
ShowOSD = true
ScreenAspectTop = 0
ScreenAspectBot = 0
ScreenFilter = {str(pixel_filter).lower()}
IntegerScaling = {str(integer_scaling).lower()}
ScreenSizing = {1 if screen_layout == 'focus' else 0}
ScreenLayout = {1 if screen_layout == 'vertical' else 2}
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
    # Preserve every native hotkey/controller binding, including disabled (-1)
    # and modifier/right-hand keys. The launcher exposes only a small subset.
    config=config.split('[Instance0.Keyboard]')[0]+'[Instance0.Keyboard]\n'
    config+=''.join(f'{name} = {value}\n' for name,value in values.items())
    config+='\n[Instance0.Joystick]\n'+''.join(f'{name} = {value}\n' for name,value in profile['Joystick'].items())
    destination.write_text(config, encoding="utf-8")
    return destination


def _toml_path(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/").replace('"', '\\"')


def launch(executable: Path, rom: Path, *, fullscreen: bool = True, player: str = 'Optimus', request: Path | None = None, mirror: Path | None = None, website: str = '') -> subprocess.Popen:
    if not rom.is_file():
        raise FileNotFoundError("Die ausgewählte ROM wurde nicht gefunden.")
    command = [str(executable)]
    if fullscreen:
        command.append("--fullscreen")
    command.append(str(rom))
    env=os.environ.copy()
    env.pop('SOULLINK_MIRROR',None)
    env['SOULLINK_PLAYER']=player
    if request is not None: env['SOULLINK_REQUEST']=str(request)
    if request is not None: env['SOULLINK_TEAM']=str(request.with_suffix('.team'))
    # Video is retired, including inherited or legacy caller configuration.
    if website: env['SOULLINK_WEBSITE']=website
    return subprocess.Popen(command, cwd=str(executable.parent),env=env)


def read_runtime_settings(executable: Path) -> dict:
    """Import explicit native changes after exit; never read/write game saves."""
    config=tomllib.loads((portable_directory(executable)/'melonDS.toml').read_text())
    window=config['Instance0']['Window0']
    scale=int(config['3D']['GL']['ScaleFactor'])
    fps=round(config.get('TargetFPS',60)) if config.get('LimitFPS',True) else 0
    volume=round(config['Instance0']['Audio']['Volume']*100/256)
    if not 1<=scale<=16 or fps not in (0,60,90,120) or not 0<=volume<=100:
        raise ValueError('Ungültige Emulator-Einstellungen.')
    keys={}
    reverse={value:key for key,value in QT_KEYS.items()}
    for name,value in config['Instance0']['Keyboard'].items():
        if name in DEFAULT_KEYS:
            if value in reverse: keys[name]=reverse[value]
            elif 32<=value<=126: keys[name]=chr(value)
            elif type(value) is int and -(1<<31)<=value<(1<<31): keys[name]='QT:'+str(value)
    return {'scale':scale,'fps':fps,'volume':volume,'keys':keys,
            'pixel_filter':bool(window.get('ScreenFilter',False)),
            'integer_scaling':bool(window.get('IntegerScaling',False)),
            'screen_layout':'vertical' if window.get('ScreenLayout')==1 else 'focus' if window.get('ScreenSizing')==1 else 'horizontal'}


def copy_emulator(source: Path, destination: Path) -> Path:
    """Optional helper for making an isolated portable emulator copy."""
    if platform.system() == 'Darwin' and source.parent.name == 'MacOS' and source.parents[1].name == 'Contents':
        source = source.parents[2]
    binary=find_executable(source)
    fingerprint=hashlib.sha256(binary.read_bytes()).hexdigest()[:12]
    destination=destination/('build-'+fingerprint)
    destination.mkdir(parents=True,exist_ok=True)
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


def preferred_emulator(selected: str, bundled: Path) -> str:
    """Portable updates must not keep launching an older bundled emulator."""
    previous=Path(selected) if selected else None
    managed=previous and ((previous.parent/'focus-version.txt').is_file()
                         or previous.parent.name=='Emulator' and previous.name in ('melonDS.exe','melonDS.app'))
    if bundled.exists() and (not previous or not previous.exists() or managed):return str(bundled)
    return selected
