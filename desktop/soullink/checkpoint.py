"""Prepare named copies of verified HGSS in-game checkpoints."""
from pathlib import Path
import binascii
import gzip
import hashlib
import struct

from .save_reader import (GENERAL_SIZE, PARTITION_SIZE, _active, _decrypt,
                          _encrypt, _text, parse_save, read_save)

POSTSTARTER_TEMPLATE_SHA256 = 'cf16abacfde8058f3e5190c19ab2b845c2c439812e5594c45e6af7216809d489'


def named_checkpoint(source: Path, target: Path, trainer: str) -> None:
    state = read_save(source)
    if state.gender != 0 or state.party:
        raise ValueError("Der Checkpoint muss männlich und noch ohne Starter sein.")
    if not 1 <= len(trainer) <= 7 or not trainer.isascii() or not trainer.isalpha():
        raise ValueError("Trainername: 1–7 lateinische Buchstaben.")
    data = bytearray(source.read_bytes())
    name = [0x12B + ord(c) - ord('A') if c.isupper() else 0x145 + ord(c) - ord('a') for c in trainer]
    encoded = struct.pack('<' + 'H' * (len(name) + 1), *name, 0xFFFF).ljust(16, b'\x00')
    for base in (0, PARTITION_SIZE):
        block = data[base:base + GENERAL_SIZE]
        if binascii.crc_hqx(block[:-16], 0xFFFF) != struct.unpack_from('<H', block, GENERAL_SIZE - 2)[0]:
            continue
        data[base + 0x64:base + 0x74] = encoded
        data[base + 0x7C] = 0
        struct.pack_into('<H', data, base + GENERAL_SIZE - 2,
                         binascii.crc_hqx(data[base:base + GENERAL_SIZE - 16], 0xFFFF))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    if read_save(target).trainer != trainer:
        raise ValueError("Trainername konnte nicht verifiziert werden.")


def _experience(level: int, growth: int) -> int:
    n = level
    if growth == 0:  # medium fast
        return n ** 3
    if growth == 1:  # erratic
        if n <= 50: return n ** 3 * (100 - n) // 50
        if n <= 68: return n ** 3 * (150 - n) // 100
        if n <= 98: return n ** 3 * ((1911 - 10 * n) // 3) // 500
        return n ** 3 * (160 - n) // 100
    if growth == 2:  # fluctuating
        if n <= 15: return n ** 3 * ((n + 1) // 3 + 24) // 50
        if n <= 36: return n ** 3 * (n + 14) // 50
        return n ** 3 * (n // 2 + 32) // 50
    if growth == 3:  # medium slow
        return max(0, 6 * n ** 3 // 5 - 15 * n ** 2 + 100 * n - 140)
    if growth == 4:  # fast
        return 4 * n ** 3 // 5
    if growth == 5:  # slow
        return 5 * n ** 3 // 4
    raise ValueError('Unbekannte Erfahrungskurve im ROM-Paket.')


def _calculated_stats(mon: bytearray, base_stats: list[int], level: int) -> list[int]:
    iv32 = struct.unpack_from('<I', mon, 0x38)[0]
    ivs = [(iv32 >> shift) & 31 for shift in (0, 5, 10, 15, 20, 25)]
    evs = list(mon[0x18:0x1E])
    hp = ((2 * base_stats[0] + ivs[0] + evs[0] // 4) * level) // 100 + level + 10
    if struct.unpack_from('<H', mon, 8)[0] == 292: hp = 1
    nature = struct.unpack_from('<I', mon, 0)[0] % 25
    raised, lowered = divmod(nature, 5)
    result = [hp]
    for index, base in enumerate(base_stats[1:]):
        value = ((2 * base + ivs[index + 1] + evs[index + 1] // 4) * level) // 100 + 5
        if raised != lowered:
            if index == raised: value = value * 110 // 100
            elif index == lowered: value = value * 90 // 100
        result.append(value)
    return result


def _starter_moves(pokemon: dict, moves: dict, level: int) -> list[int]:
    learned: list[int] = []
    for entry in pokemon.get('learnset', []):
        if (not isinstance(entry, list) or len(entry) != 2
                or type(entry[0]) is not int or type(entry[1]) is not int):
            raise ValueError('Ungültige Starter-Attacken im ROM-Paket.')
        learned_level, move = entry
        if learned_level > level or move <= 0: continue
        if move not in learned: learned.append(move)
    selected = learned[-4:]
    if not selected or any(str(move) not in moves for move in selected):
        raise ValueError('Starter-Attacken fehlen im ROM-Paket.')
    return selected


def starter_checkpoint_bytes(template: Path, player: str, species: int, metadata: dict) -> bytes:
    """Create the requested T1 at the exact post-selection sample position."""
    from .identity import NAMES, name_bytes
    if player not in NAMES or not 1 <= species <= 493:
        raise ValueError('Ungültiger Spieler oder Starter.')
    with gzip.open(template, 'rb') as source:
        original = source.read()
    if hashlib.sha256(original).hexdigest() != POSTSTARTER_TEMPLATE_SHA256:
        raise ValueError('Die bereinigte T1-Startvorlage wurde verändert oder beschädigt.')
    initial = parse_save(original)
    if initial.trainer != 'SOULLNK' or len(initial.party) != 1 or initial.party[0].nickname != 'T1':
        raise ValueError('Der spätere Start-Spielstand ist ungültig.')
    pokemon = next((item for item in metadata.get('pokemon', [])
                    if isinstance(item, dict) and item.get('species') == species), None)
    moves = metadata.get('moves', {})
    if metadata.get('format') != 2 or pokemon is None or not isinstance(moves, dict):
        raise ValueError('Die Starterdaten passen nicht zur ROM.')
    base_stats = pokemon.get('baseStats')
    abilities = pokemon.get('abilities')
    if (not isinstance(base_stats, list) or len(base_stats) != 6
            or any(type(value) is not int or value <= 0 for value in base_stats)
            or not isinstance(abilities, list) or len(abilities) != 2
            or any(type(value) is not int or value < 0 for value in abilities)):
        raise ValueError('Die Starterwerte im ROM-Paket sind ungültig.')

    data = bytearray(original)
    valid = []
    for partition in (0, 1):
        base = partition * PARTITION_SIZE
        block = data[base:base + GENERAL_SIZE]
        if binascii.crc_hqx(block[:-16], 0xFFFF) == struct.unpack_from('<H', block, GENERAL_SIZE - 2)[0]:
            valid.append(partition)
    active = _active(original, 0, GENERAL_SIZE)
    base = active * PARTITION_SIZE
    if data[base + 0x94] != 1:
        raise ValueError('Der spätere Start-Spielstand enthält nicht genau ein Pokémon.')
    start = base + 0x98
    mon = _decrypt(data[start:start + 236])
    if _text(mon, 0x48, 11) != 'T1' or mon[0x8C] != 5:
        raise ValueError('T1 im späteren Start-Spielstand ist nicht auf Level 5.')

    level = 5
    struct.pack_into('<H', mon, 8, species)
    struct.pack_into('<I', mon, 0x10, _experience(level, int(pokemon.get('growth', -1))))
    mon[0x14] = 70
    pid = struct.unpack_from('<I', mon, 0)[0]
    mon[0x15] = abilities[1] if pid & 1 and abilities[1] else abilities[0]
    selected_moves = _starter_moves(pokemon, moves, level)
    padded_moves = selected_moves + [0] * (4 - len(selected_moves))
    struct.pack_into('<4H', mon, 0x28, *padded_moves)
    mon[0x30:0x34] = bytes([int(moves[str(move)]['pp']) if move else 0 for move in padded_moves])
    mon[0x34:0x38] = bytes(4)
    ratio = int(pokemon.get('genderRatio', -1))
    if ratio == 255: gender = 2
    elif ratio == 254: gender = 1
    elif ratio == 0: gender = 0
    elif 1 <= ratio <= 253: gender = 1 if (pid & 0xFF) < ratio else 0
    else: raise ValueError('Ungültiges Geschlechterverhältnis im ROM-Paket.')
    mon[0x40] = (mon[0x40] & ~0x06) | (gender << 1)
    mon[0x68:0x78] = name_bytes(NAMES[player])
    mon[0x88:0x8C] = bytes(4)
    mon[0x8C] = level
    stats = _calculated_stats(mon, base_stats, level)
    struct.pack_into('<7H', mon, 0x8E, stats[0], *stats)
    data[start:start + 236] = _encrypt(mon)

    encoded_name = name_bytes(NAMES[player])
    for partition in valid:
        partition_base = partition * PARTITION_SIZE
        data[partition_base + 0x64:partition_base + 0x74] = encoded_name
        struct.pack_into('<H', data, partition_base + GENERAL_SIZE - 2,
                         binascii.crc_hqx(data[partition_base:partition_base + GENERAL_SIZE - 16], 0xFFFF))
    result = bytes(data)
    checked = parse_save(result)
    if (checked.trainer != NAMES[player] or len(checked.party) != 1
            or checked.party[0].species != species or checked.party[0].nickname != 'T1'
            or checked.party[0].level != level or checked.party[0].hp != checked.party[0].max_hp):
        raise ValueError('Der spätere Start-Spielstand konnte nicht verifiziert werden.')
    return result
