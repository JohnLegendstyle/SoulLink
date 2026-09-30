from __future__ import annotations

import struct
import binascii
from dataclasses import dataclass
from pathlib import Path


GENERAL_SIZE = 0xF628
STORAGE_SIZE = 0x12310
PARTITION_SIZE = 0x40000
STORAGE_START = 0xF700
BLOCK_POSITION = (
    (0,1,2,3),(0,1,3,2),(0,2,1,3),(0,3,1,2),(0,2,3,1),(0,3,2,1),
    (1,0,2,3),(1,0,3,2),(2,0,1,3),(3,0,1,2),(2,0,3,1),(3,0,2,1),
    (1,2,0,3),(1,3,0,2),(2,1,0,3),(3,1,0,2),(2,3,0,1),(3,2,0,1),
    (1,2,3,0),(1,3,2,0),(2,1,3,0),(3,1,2,0),(2,3,1,0),(3,2,1,0),
)


@dataclass(frozen=True)
class Pokemon:
    uid: str
    species: int
    nickname: str
    level: int | None
    hp: int | None
    max_hp: int | None
    met_location: int | None = None
    origin_game: int | None = None
    is_egg: bool = False
    egg_location: int = 0

    def api(self) -> dict[str, object]:
        return {
            "uid": self.uid, "species": self.species, "nickname": self.nickname,
            "level": self.level, "hp": self.hp, "maxHp": self.max_hp,
            "metLocation": self.met_location, "originGame": self.origin_game,
            "isEgg": self.is_egg, "eggLocation": self.egg_location,
        }


@dataclass(frozen=True)
class SaveState:
    trainer: str
    gender: int
    party: list[Pokemon]
    owned: list[Pokemon]


def _u32(data: bytes | bytearray, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def _active(data: bytes, begin: int, length: int) -> int:
    valid = []
    for partition in (0, 1):
        block = data[begin + partition * PARTITION_SIZE:begin + partition * PARTITION_SIZE + length]
        if binascii.crc_hqx(block[:-0x10], 0xFFFF) == struct.unpack_from('<H', block, length - 2)[0]:
            valid.append(partition)
    if not valid:
        raise ValueError("Spielstand wird gerade gespeichert oder ist beschädigt.")
    if len(valid) == 1:
        return valid[0]
    a = begin + length - 0x14
    b = a + PARTITION_SIZE
    one = (_u32(data, a), _u32(data, a + 4))
    two = (_u32(data, b), _u32(data, b + 4))
    if one[0] == 0xFFFFFFFF and two[0] != 0xFFFFFFFE:
        return 1
    if two[0] == 0xFFFFFFFF and one[0] != 0xFFFFFFFE:
        return 0
    return 0 if one >= two else 1


def _crypt(chunk: bytearray, start: int, end: int, seed: int) -> None:
    for offset in range(start, end, 2):
        seed = (0x41C64E6D * seed + 0x6073) & 0xFFFFFFFF
        value = struct.unpack_from("<H", chunk, offset)[0] ^ (seed >> 16)
        struct.pack_into("<H", chunk, offset, value)


def _decrypt(raw: bytes) -> bytearray:
    data = bytearray(raw)
    pid = _u32(data, 0)
    checksum = struct.unpack_from("<H", data, 6)[0]
    _crypt(data, 8, 136, checksum)
    if len(data) > 136:
        _crypt(data, 136, len(data), pid)
    order = BLOCK_POSITION[((pid >> 13) & 31) % 24]
    blocks = [bytes(data[8 + i * 32: 40 + i * 32]) for i in range(4)]
    # The table maps logical block -> encrypted slot, not the reverse.
    data[8:136] = b"".join(blocks[slot] for slot in order)
    return data


def _encrypt(plain: bytes | bytearray) -> bytes:
    """Return a Gen-IV encrypted Pokémon from canonical logical block order."""
    if len(plain) not in (136, 236):
        raise ValueError("Ein Pokémon-Datensatz muss 136 oder 236 Bytes groß sein.")
    data = bytearray(plain)
    pid = _u32(data, 0)
    checksum = sum(struct.unpack('<64H', data[8:136])) & 0xFFFF
    struct.pack_into('<H', data, 6, checksum)
    order = BLOCK_POSITION[((pid >> 13) & 31) % 24]
    logical = [bytes(data[8 + i * 32:40 + i * 32]) for i in range(4)]
    physical = [b''] * 4
    for logical_index, physical_slot in enumerate(order):
        physical[physical_slot] = logical[logical_index]
    data[8:136] = b''.join(physical)
    _crypt(data, 8, 136, checksum)
    if len(data) > 136:
        _crypt(data, 136, len(data), pid)
    return bytes(data)


def _text(data: bytes | bytearray, offset: int, chars: int) -> str:
    result = []
    for i in range(chars):
        value = struct.unpack_from("<H", data, offset + i * 2)[0]
        if value in (0, 0xFFFF):
            break
        if 0x121 <= value <= 0x12A:
            result.append(chr(ord('0') + value - 0x121))
        elif 0x12B <= value <= 0x144:
            result.append(chr(ord('A') + value - 0x12B))
        elif 0x145 <= value <= 0x15E:
            result.append(chr(ord('a') + value - 0x145))
        else:
            accents = "ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ⑧ØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõö⑨øùúûüýþÿŒœ"
            result.append(accents[value - 0x15F] if 0x15F <= value < 0x15F + len(accents) else {0x1DE:' ',0x1BB:'♂',0x1BC:'♀',0x1BD:'+',0x1BE:'-',0x1AD:',',0x1AE:'.',0x1AB:'!',0x1AC:'?'}.get(value, '?'))
    return "".join(result).replace("\ue08e", "♂").replace("\ue08f", "♀")


def _pokemon(raw: bytes, party: bool) -> Pokemon | None:
    if not raw or raw == bytes(len(raw)) or raw == b"\xff" * len(raw):
        return None
    data = _decrypt(raw)
    if sum(struct.unpack('<64H', data[8:136])) & 0xFFFF != struct.unpack_from('<H', data, 6)[0]:
        return None
    species = struct.unpack_from("<H", data, 8)[0]
    if not 1 <= species <= 493:
        return None
    pid = _u32(data, 0)
    tid = _u32(data, 0x0C)
    uid = f"{pid:08x}-{tid:08x}"
    nickname = _text(data, 0x48, 11)
    # Gen IV extended Pt/HGSS locations supersede DP's Faraway Place marker.
    # Source: PKHeX.Core/PKM/PK4.cs and Shared/G4PKM.cs (read-only parsing).
    met = struct.unpack_from('<H', data, 0x46)[0] or struct.unpack_from('<H', data, 0x80)[0]
    egg = struct.unpack_from('<H', data, 0x44)[0] or struct.unpack_from('<H', data, 0x7E)[0]
    encounter = (met or None, data[0x5F], bool(_u32(data, 0x38) & (1 << 30)), egg)
    if party:
        return Pokemon(uid, species, nickname, data[0x8C],
                       struct.unpack_from("<H", data, 0x8E)[0],
                       struct.unpack_from("<H", data, 0x90)[0], *encounter)
    return Pokemon(uid, species, nickname, None, None, None, *encounter)


def read_save(path: str | Path) -> SaveState:
    return parse_save(Path(path).read_bytes())


def parse_save(data: bytes) -> SaveState:
    if len(data) != 0x80000:
        raise ValueError("Der Spielstand muss genau 512 KiB groß sein.")
    if data == b"\xff" * len(data):
        raise ValueError("Der Spielstand ist noch leer.")
    gpart = _active(data, 0, GENERAL_SIZE)
    spart = _active(data, STORAGE_START, STORAGE_SIZE)
    general = gpart * PARTITION_SIZE
    storage = spart * PARTITION_SIZE + STORAGE_START
    trainer = _text(data, general + 0x64, 8)
    gender = data[general + 0x7C]
    count = min(data[general + 0x94], 6)
    party: list[Pokemon] = []
    for index in range(count):
        start = general + 0x98 + index * 236
        pokemon = _pokemon(data[start:start + 236], True)
        if pokemon:
            party.append(pokemon)
    boxes: list[Pokemon] = []
    for box in range(18):
        base = storage + box * 0x1000
        for slot in range(30):
            start = base + slot * 136
            pokemon = _pokemon(data[start:start + 136], False)
            if pokemon:
                boxes.append(pokemon)
    known = {p.uid for p in party}
    return SaveState(trainer, gender, party, party + [p for p in boxes if p.uid not in known])
