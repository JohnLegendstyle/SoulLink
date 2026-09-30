#!/usr/bin/env python3
"""Sanitize a regular HGSS save or SRAM extracted from a melonDS savestate."""
from __future__ import annotations

import argparse
import binascii
import gzip
import io
import struct
import sys
from pathlib import Path

DESKTOP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DESKTOP))

from soullink.identity import name_bytes  # noqa: E402
from soullink.save_reader import (  # noqa: E402
    GENERAL_SIZE,
    PARTITION_SIZE,
    _active,
    _decrypt,
    _encrypt,
    parse_save,
)

GENERIC_NAME = "SOULLNK"
GENERIC_TRAINER_ID = 0x534C0001


def extract_hgss_sram(state: bytes) -> bytes:
    """Read the retail-cart SRAM from the NDCS section of a melonDS v13 state."""
    if len(state) < 16 or state[:4] != b"MELN":
        raise ValueError("Keine melonDS-Savestate (MELN) ausgewählt.")
    major, _minor, declared = struct.unpack_from("<HHI", state, 4)
    if major != 13 or declared != len(state):
        raise ValueError("Die Savestate stammt nicht aus dem unterstützten melonDS-1.1-Format.")
    offset = 16
    found: bytes | None = None
    while offset < len(state):
        if offset + 16 > len(state):
            raise ValueError("Beschädigter melonDS-Abschnitt.")
        magic = state[offset:offset + 4]
        length = struct.unpack_from("<I", state, offset + 4)[0]
        if length < 16 or offset + length > len(state):
            raise ValueError("Ungültige Abschnittslänge in der Savestate.")
        if magic == b"NDCS":
            content = offset + 16
            if length < 32:
                raise ValueError("Der Spielkarten-Abschnitt ist unvollständig.")
            sram_length = struct.unpack_from("<I", state, content + 12)[0]
            start = content + 16
            end = start + sram_length
            if sram_length != 0x80000 or end > offset + length:
                raise ValueError("Die Savestate enthält keinen 512-KiB-SoulSilver-Spielstand.")
            if found is not None:
                raise ValueError("Die Savestate enthält mehrere Spielkarten-Abschnitte.")
            found = state[start:end]
        offset += length
    if offset != len(state) or found is None:
        raise ValueError("Der SoulSilver-Spielstand fehlt in der Savestate.")
    return found


def sanitize_checkpoint(original: bytes) -> bytes:
    """Keep the story position while replacing original player/Pokémon identity."""
    state = parse_save(original)
    if state.gender != 0 or len(state.party) != 1 or state.party[0].nickname != "T1":
        raise ValueError("Die Vorlage muss einen männlichen Trainer mit genau einem T1 enthalten.")

    data = bytearray(original)
    valid: list[int] = []
    for partition in (0, 1):
        base = partition * PARTITION_SIZE
        block = data[base:base + GENERAL_SIZE]
        if binascii.crc_hqx(block[:-16], 0xFFFF) == struct.unpack_from(
            "<H", block, GENERAL_SIZE - 2
        )[0]:
            valid.append(partition)
            data[base + 0x64:base + 0x74] = name_bytes(GENERIC_NAME)
            struct.pack_into("<I", data, base + 0x74, GENERIC_TRAINER_ID)
            data[base + 0x7C] = 0

    active = _active(original, 0, GENERAL_SIZE)
    base = active * PARTITION_SIZE
    start = base + 0x98
    mon = _decrypt(data[start:start + 236])

    # Deterministic, non-personal Bulbasaur shell. The launcher replaces every
    # species-dependent field after the player chooses T1.
    struct.pack_into("<I", mon, 0x00, 0x12345678)
    struct.pack_into("<H", mon, 0x08, 1)
    struct.pack_into("<H", mon, 0x0A, 0)
    struct.pack_into("<I", mon, 0x0C, GENERIC_TRAINER_ID)
    struct.pack_into("<I", mon, 0x10, 125)
    mon[0x14:0x17] = bytes((70, 65, 0))
    mon[0x18:0x28] = bytes(16)
    struct.pack_into("<4H", mon, 0x28, 33, 45, 0, 0)
    mon[0x30:0x34] = bytes((35, 40, 0, 0))
    mon[0x34:0x38] = bytes(4)
    ivs = sum(15 << shift for shift in (0, 5, 10, 15, 20, 25)) | (1 << 31)
    struct.pack_into("<I", mon, 0x38, ivs)
    mon[0x3C:0x40] = bytes(4)
    mon[0x40] &= ~0x06
    mon[0x48:0x5E] = bytes(22)
    struct.pack_into("<3H", mon, 0x48, 0x13E, 0x122, 0xFFFF)
    mon[0x68:0x78] = name_bytes(GENERIC_NAME)
    mon[0x88:0x8C] = bytes(4)
    mon[0x8C] = 5
    struct.pack_into("<7H", mon, 0x8E, 20, 20, 11, 11, 13, 13, 13)
    data[start:start + 236] = _encrypt(mon)

    for partition in valid:
        partition_base = partition * PARTITION_SIZE
        struct.pack_into(
            "<H",
            data,
            partition_base + GENERAL_SIZE - 2,
            binascii.crc_hqx(data[partition_base:partition_base + GENERAL_SIZE - 16], 0xFFFF),
        )

    result = bytes(data)
    checked = parse_save(result)
    if (
        checked.trainer != GENERIC_NAME
        or len(checked.owned) != 1
        or checked.party[0].species != 1
        or checked.party[0].nickname != "T1"
        or checked.party[0].level != 5
    ):
        raise ValueError(f"Die bereinigte Startvorlage konnte nicht verifiziert werden: {checked!r}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("savestate", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    original = args.savestate.read_bytes()
    if original[:4] == b"MELN":
        original = extract_hgss_sram(original)
    sanitized = sanitize_checkpoint(original)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    compressed = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=compressed, mtime=0) as target:
        target.write(sanitized)
    args.output.write_bytes(compressed.getvalue())


if __name__ == "__main__":
    main()
