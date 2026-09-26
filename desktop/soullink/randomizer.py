from __future__ import annotations

import json
import os
import re
import secrets
import hashlib
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from .save_reader import read_save


UPSTREAM_VERSION = "4.6.1"
UPSTREAM_URL = (
    "https://github.com/Ajarmar/universal-pokemon-randomizer-zx/releases/"
    "download/v4.6.1/PokeRandoZX-v4_6_1.zip"
)


@dataclass(frozen=True)
class PlayerPack:
    player: str
    trainer: str
    rom: Path
    save: Path | None
    seed: int
    starters: list[dict[str, object]]


def runtime_root() -> Path:
    embedded = Path(getattr(__import__("sys"), "_MEIPASS", Path(__file__).parents[1]))
    return embedded / "randomizer"


def install_root() -> Path:
    if getattr(sys, 'frozen', False):
        exe = Path(sys.executable).resolve()
        return exe.parents[3] if sys.platform == 'darwin' else exe.parent
    return Path(__file__).parents[1]


def java_binary() -> str:
    root = runtime_root()
    names = [install_root() / 'Runtime' / 'bin' / name for name in ('java.exe', 'java')]
    names += [root / "jre" / "bin" / "java.exe", root / "jre" / "bin" / "java"]
    for candidate in names:
        if candidate.is_file():
            return str(candidate)
    found = shutil.which("java")
    if found:
        return found
    raise RuntimeError("Java fehlt. Bitte Java 17 oder neuer installieren.")


def classpath() -> str:
    root = runtime_root()
    jar = root / "PokeRandoZX.jar"
    classes = root / "classes"
    if not jar.is_file():
        raise RuntimeError("PokeRandoZX.jar fehlt im App-Paket.")
    if not (classes / "soullink" / "StarterRandomizer.class").is_file():
        raise RuntimeError("Der Soul-Link-Randomizer wurde nicht mitgeliefert.")
    return os.pathsep.join((str(classes), str(jar)))


def randomize(input_rom: Path, output_rom: Path, seed: int, mode: str = 'adventure') -> list[dict[str, object]]:
    command = [
        java_binary(), "-Dfile.encoding=UTF-8", "-cp", classpath(), "soullink.StarterRandomizer",
        str(input_rom), str(output_rom), str(seed), mode,
    ]
    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=180)
    if result.returncode:
        detail = (result.stderr or result.stdout).strip().splitlines()[-1:]
        raise RuntimeError(detail[0] if detail else "Die ROM konnte nicht randomisiert werden.")
    match = re.search(r"SOULLINK_STARTERS=(.+)", result.stdout)
    if not match:
        raise RuntimeError("Die Starterauswahl konnte nicht gelesen werden.")
    starters = []
    for item in match.group(1).strip().split(","):
        number, name = item.split(":", 1)
        starters.append({"species": int(number), "name": name})
    return starters


def create_round(
    original_rom: Path,
    destination: Path,
    checkpoints: Path,
    mode: str = 'adventure',
) -> tuple[Path, list[PlayerPack]]:
    original_rom = original_rom.expanduser().resolve()
    with original_rom.open('rb') as source:
        header = source.read(16)
    if header[:12] != b"POKEMON SS\x00\x00" or header[12:16] != b"IPGD":
        raise ValueError("Bitte die bereitgestellte deutsche SoulSilver-ROM auswählen.")
    for trainer in ('Optimus', 'Bee'):
        state = read_save(checkpoints / f'{trainer}.sav')
        if state.trainer != trainer or state.gender != 0 or state.party:
            raise ValueError(f"Der Start-Spielstand für {trainer} fehlt oder ist ungültig.")
    round_dir = destination.expanduser().resolve() / (datetime.now().strftime("Runde-%Y-%m-%d_%H-%M-%S") + '-' + secrets.token_hex(2))
    round_dir.mkdir(parents=True, exist_ok=False)
    packs: list[PlayerPack] = []
    for player, trainer in (("Optimus", "Optimus"), ("Bee", "Bee")):
        player_dir = round_dir / player
        player_dir.mkdir()
        rom = player_dir / f"SoulSilver_{player}.nds"
        seed = secrets.randbits(63)
        starters = randomize(original_rom, rom, seed, mode)
        template = checkpoints / f"{trainer}.sav"
        save = player_dir / f"SoulSilver_{player}.sav"
        shutil.copy2(template, save)
        packs.append(PlayerPack(player, trainer, rom, save, seed, starters))

    manifest = {
        "format": 1,
        "mode": mode,
        "createdAt": datetime.now().astimezone().isoformat(),
        "source": {"file": original_rom.name, "sha256": hashlib.sha256(original_rom.read_bytes()).hexdigest()},
        "players": [
            {
                "player": p.player, "trainer": p.trainer, "seed": p.seed,
                "rom": p.rom.relative_to(round_dir).as_posix(),
                "save": p.save.relative_to(round_dir).as_posix() if p.save else None,
                "starters": p.starters,
            }
            for p in packs
        ],
    }
    (round_dir / "runde.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    (round_dir / "START.txt").write_text(
        "Soul Link – private Spielrunde\n\n"
        "Optimus öffnet seinen Ordner, Eddie den Ordner Bee. "
        "Die Starter bitte erst im Spiel selbst auswählen.\n",
        encoding="utf-8",
    )
    return round_dir, packs


def load_round(manifest: Path) -> list[PlayerPack]:
    manifest = manifest.expanduser().resolve()
    data = json.loads(manifest.read_text(encoding='utf-8'))
    if data.get('format') != 1:
        raise ValueError('Unbekanntes Rundenformat.')
    packs = []
    for p in data['players']:
        if p['player'] not in ('Optimus', 'Bee'):
            raise ValueError('Unbekannter Spieler in der Runde.')
        rom = (manifest.parent / p['rom']).resolve()
        save = (manifest.parent / p['save']).resolve()
        if not rom.is_relative_to(manifest.parent) or not save.is_relative_to(manifest.parent):
            raise ValueError('Ungültiger Dateipfad in der Runde.')
        if not rom.is_file() or not save.is_file():
            raise ValueError('ROM oder Spielstand fehlen. Bitte den ganzen Runden-Ordner öffnen.')
        packs.append(PlayerPack(p['player'], p['trainer'], rom, save, int(p['seed']), p['starters']))
    if {p.player for p in packs} != {'Optimus','Bee'} or len(packs) != 2:
        raise ValueError('Die Runde muss Optimus und Bee enthalten.')
    return packs
