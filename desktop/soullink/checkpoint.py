"""Prepare named copies of a verified HGSS in-game checkpoint."""
from pathlib import Path
import binascii
import struct

from .save_reader import GENERAL_SIZE, PARTITION_SIZE, read_save


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
