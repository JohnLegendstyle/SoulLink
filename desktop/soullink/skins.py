"""Local, reversible overworld skins. No saves, game logic or Pokémon edited."""
from __future__ import annotations

import json
import os
import re
import struct
import sys
import tempfile
from pathlib import Path

SKINS = {'Optimus':'optimus-prime', 'Bee':'bumblebee'}
# Ethan's normal walking/running, Rocket-disguise and alternate walking set.
# NPCs, the female protagonist and special-action sheets are intentionally untouched.
TARGETS = {69: 'hero', 95: 'rhero', 213: 'hero'}


def load_skin(player: str) -> dict:
    if player not in SKINS:
        raise ValueError('Unbekannter Spieler.')
    root = Path(getattr(sys, '_MEIPASS', Path(__file__).parents[1]))
    data = json.loads((root/'assets'/'skins'/f'{SKINS[player]}.json').read_text())
    if data.get('format') != 1 or data.get('size') != 32 or len(data['palette']) != 16 or len(data['frames']) != 16:
        raise ValueError('Ungültiges Figuren-Paket.')
    if any(len(c)!=3 or any(type(v)!=int or not 0<=v<=31 for v in c) for c in data['palette']):
        raise ValueError('Ungültige Figuren-Farben.')
    data['frames'] = [bytes.fromhex(f) for f in data['frames']]
    if any(len(f)!=512 for f in data['frames']):
        raise ValueError('Ungültige Figuren-Animation.')
    return data


def patch_rom_bytes(original: bytes, player: str) -> bytes:
    # Lazy imports let dependency-free manifest/save tests run before packaging.
    from ndspy.fnt import load
    from ndspy.texture import NSBTX, TextureFormat
    if original[:16] != b'POKEMON SS\0\0IPGD':
        raise ValueError('Figuren-Paket benötigt die deutsche SoulSilver-ROM.')
    skin = load_skin(player)
    fnt, fnt_size, fat, fat_size = struct.unpack_from('<4I',original,0x40)
    if fnt+fnt_size > len(original) or fat+fat_size > len(original):
        raise ValueError('Ungültige ROM-Dateitabelle.')
    file_id = load(original[fnt:fnt+fnt_size]).idOf('a/0/8/1')
    if file_id is None or file_id*8+8 > fat_size:
        raise ValueError('Figuren-Archiv fehlt.')
    start, end = struct.unpack_from('<II',original,fat+file_id*8)
    archive = original[start:end]
    if not 0 <= start < end <= len(original) or archive[:4] != b'NARC' or archive[16:20] != b'BTAF':
        raise ValueError('Ungültiges Figuren-Archiv.')
    table_size, count = struct.unpack_from('<II',archive,20)
    names = 16+table_size
    payload = names+struct.unpack_from('<I',archive,names+4)[0]+8
    if archive[payload-8:payload-4] != b'GMIF' or count <= max(TARGETS):
        raise ValueError('Unbekanntes Figuren-Archiv.')
    result = bytearray(original)
    for index, prefix in TARGETS.items():
        lo, hi = struct.unpack_from('<II',archive,28+index*8)
        lo, hi = payload+lo, payload+hi
        if not payload <= lo < hi <= len(archive):
            raise ValueError('Ungültige Figuren-Grenzen.')
        texture = NSBTX(archive[lo:hi])
        if len(texture.textures)!=32 or len(texture.palettes)!=1:
            raise ValueError('Unbekannte Figuren-Animation.')
        replacement = bytearray(archive[lo:hi])
        tex0 = struct.unpack_from('<I',replacement,16)[0]
        capacity, info = struct.unpack_from('<HH',replacement,tex0+12)
        pixels = tex0+struct.unpack_from('<I',replacement,tex0+20)[0]
        palette = tex0+struct.unpack_from('<I',replacement,tex0+56)[0]
        entries = tex0+info+16+4*len(texture.textures)
        if pixels+capacity*8>len(replacement) or palette+32>len(replacement):
            raise ValueError('Ungültige Textur-Grenzen.')
        unique = {}
        expected = []
        for position, (name, frame) in enumerate(texture.textures):
            match = re.fullmatch(re.escape(prefix)+r'\.(\d+)',name)
            if not match or not 1<=int(match[1])<=32 or frame.size!=(32,32) or frame.format!=TextureFormat.I4:
                raise ValueError('Unbekanntes Figuren-Format.')
            data = skin['frames'][(int(match[1])-1)%16]
            if data not in unique: unique[data] = len(unique)*512
            offset = unique[data]
            if offset+512>capacity*8:
                raise ValueError('Die neue Figur passt nicht in das Grafik-Archiv.')
            replacement[pixels+offset:pixels+offset+512] = data
            struct.pack_into('<H',replacement,entries+position*8,offset//8)
            expected.append(data)
        replacement[pixels+len(unique)*512:pixels+capacity*8] = bytes(capacity*8-len(unique)*512)
        for i,(r,g,b) in enumerate(skin['palette']):
            struct.pack_into('<H',replacement,palette+i*2,r|(g<<5)|(b<<10))
        check = NSBTX(replacement)
        if [t.data1 for _,t in check.textures] != expected:
            raise ValueError('Figuren-Prüfung fehlgeschlagen.')
        result[start+lo:start+hi] = replacement.ljust(hi-lo,b'\0')
    return bytes(result)


def apply_skin(rom: Path, player: str, *, backup: bool = True) -> bool:
    """Validate fully, retain a recovery copy, then atomically replace ROM only.

    Caller must ensure the emulator is closed. Never opens any save file.
    Reapplying is a no-op. Existing recovery copies are never overwritten.
    """
    original = rom.read_bytes()
    patched = patch_rom_bytes(original, player)
    if patched == original:
        return False
    if backup:
        recovery = rom.with_suffix('.pre-transformers.nds')
        try:
            with recovery.open('xb') as stream:
                stream.write(original)
                stream.flush()
                os.fsync(stream.fileno())
        except FileExistsError:
            pass
    fd, temporary = tempfile.mkstemp(prefix=rom.stem+'.', suffix='.tmp', dir=rom.parent)
    try:
        with os.fdopen(fd,'wb') as stream:
            stream.write(patched)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary,rom)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)
    return True
