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
    selected_starter: int | None = None


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


def battle_metadata_path(rom: Path) -> Path:
    return rom.with_suffix('.soullink.json')


def _valid_battle_metadata(path: Path) -> bool:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        moves = data.get('moves', {})
        return data.get('format') == 1 and isinstance(moves, dict) and len(moves) >= 400
    except (OSError, ValueError, TypeError):
        return False


def ensure_battle_metadata(rom: Path) -> Path:
    destination = battle_metadata_path(rom)
    # Graphics and starter selection change the ROM timestamp but never the
    # Gen-IV move table represented by this versioned sidecar.
    if _valid_battle_metadata(destination):
        return destination
    temporary = destination.with_suffix(destination.suffix + '.new')
    temporary.unlink(missing_ok=True)
    command = [
        java_binary(), '-Dfile.encoding=UTF-8', '-cp', classpath(), 'soullink.StarterRandomizer',
        '--describe', str(rom), str(temporary),
    ]
    result = subprocess.run(
        command, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=90,
    )
    if result.returncode or not _valid_battle_metadata(temporary):
        temporary.unlink(missing_ok=True)
        detail = (result.stderr or result.stdout).strip().splitlines()[-1:]
        raise RuntimeError(detail[0] if detail else 'Kampfdaten konnten nicht gelesen werden.')
    os.replace(temporary, destination)
    return destination


def choose_starter(pack: PlayerPack, index: int, manifest: Path) -> PlayerPack:
    if not 0 <= index < len(pack.starters):
        raise ValueError('Bitte einen der drei Starter auswählen.')
    if pack.save and read_save(pack.save).owned:
        raise ValueError('Diese Runde wurde bereits begonnen. Der Starter wird nicht nachträglich geändert.')

    data = json.loads(manifest.read_text(encoding='utf-8'))
    players = [player for player in data.get('players', []) if player.get('player') == pack.player]
    if len(players) != 1:
        raise ValueError('Die Runde passt nicht eindeutig zu diesem Spieler.')

    species = int(pack.starters[index]['species'])
    original = pack.rom.with_suffix('.starter-options.nds')
    if not original.exists():
        shutil.copy2(pack.rom, original)
    temporary = pack.rom.with_suffix('.starter-choice.new.nds')
    rollback = pack.rom.with_suffix('.starter-rollback.nds')
    temporary.unlink(missing_ok=True)
    rollback.unlink(missing_ok=True)
    result = subprocess.run(
        [java_binary(), '-Dfile.encoding=UTF-8', '-cp', classpath(), 'soullink.StarterRandomizer',
         '--select', str(original), str(temporary), str(species)],
        capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=180,
    )
    if result.returncode or not temporary.is_file():
        temporary.unlink(missing_ok=True)
        detail = (result.stderr or result.stdout).strip().splitlines()[-1:]
        raise RuntimeError(detail[0] if detail else 'Die Starterwahl konnte nicht angewendet werden.')

    from .cloud import atomic_write
    from .jedi import rom_identity
    identity_path = pack.rom.with_suffix('.graphics-identity.json')
    previous_identity = identity_path.read_bytes() if identity_path.is_file() else None
    cloud_identity = rom_identity(pack.rom)
    try:
        os.replace(pack.rom, rollback)
        os.replace(temporary, pack.rom)
        identity = {
            'format': 1,
            'original': cloud_identity,
            'current': hashlib.sha256(pack.rom.read_bytes()).hexdigest(),
        }
        atomic_write(identity_path, json.dumps(identity).encode('utf-8'))
        players[0]['selectedStarter'] = index
        atomic_write(manifest, json.dumps(data, indent=2, ensure_ascii=False).encode('utf-8'))
    except Exception:
        if rollback.is_file():
            os.replace(rollback, pack.rom)
        if previous_identity is None:
            identity_path.unlink(missing_ok=True)
        else:
            atomic_write(identity_path, previous_identity)
        temporary.unlink(missing_ok=True)
        raise
    rollback.unlink(missing_ok=True)
    return PlayerPack(pack.player, pack.trainer, pack.rom, pack.save, pack.seed, pack.starters, index)


def randomize(input_rom: Path, output_rom: Path, seed: int, mode: str = 'adventure') -> list[dict[str, object]]:
    metadata = battle_metadata_path(output_rom)
    command = [
        java_binary(), "-Dfile.encoding=UTF-8", "-cp", classpath(), "soullink.StarterRandomizer",
        str(input_rom), str(output_rom), str(seed), mode, str(metadata),
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
    if len(starters) != 3 or not _valid_battle_metadata(metadata):
        raise RuntimeError('Starter- oder Kampfdatenprüfung fehlgeschlagen.')
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
        from .jedi import apply_jedi
        apply_jedi(rom, player, backup=False)
        template = checkpoints / f"{trainer}.sav"
        save = player_dir / f"SoulSilver_{player}.sav"
        shutil.copy2(template, save)
        from .identity import rename_save,NAMES
        rename_save(save,player)
        packs.append(PlayerPack(player, NAMES[player], rom, save, seed, starters, None))

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
        "John spielt Anakin im Ordner Optimus, Eddie spielt Obi-Wan im Ordner Bee. "
        "Den Starter zuerst im Soul-Link-Launcher auswählen und im Spiel T1 nennen.\n",
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
        selected = p.get('selectedStarter')
        if selected is not None and (type(selected) is not int or not 0 <= selected < len(p['starters'])):
            raise ValueError('Ungültige Starterwahl in der Runde.')
        packs.append(PlayerPack(p['player'], p['trainer'], rom, save, int(p['seed']), p['starters'], selected))
    if {p.player for p in packs} != {'Optimus','Bee'} or len(packs) != 2:
        raise ValueError('Die Runde muss beide Spieler (Anakin und Obi-Wan) enthalten.')
    return packs
