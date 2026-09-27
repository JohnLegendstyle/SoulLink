"""Validated, read-only team snapshots. Never substitute RAM for a game save."""
import struct
import time
from pathlib import Path
from .save_reader import _pokemon,_crypt,SaveState
from .identity import name_bytes

REGION_SIZE=0x23000

def parse_team(data:bytes, saved:SaveState):
    if len(data)!=8+REGION_SIZE+42*16 or data[:8]!=b'SLTEAM01':
        raise ValueError('Unbekannte Live-Team-Daten.')
    region=data[8:8+REGION_SIZE];headers=data[8+REGION_SIZE:]
    entries=[];end=0
    for i in range(42):
        ident,size,offset,crc,slot=struct.unpack_from('<IIIHH',headers,i*16)
        if ident!=i or not size or offset<end or offset+size>REGION_SIZE or slot>1:
            raise ValueError('Ungültige Live-Team-Struktur.')
        entries.append((offset,size));end=offset+size
    # The supported German HGSS layout is checked, never guessed from a PID.
    if entries[2][0]!=0x90 or entries[2][1]<8+6*236:
        raise ValueError('Unbekanntes Team-Layout.')
    if region[0x64:0x74]!=name_bytes(saved.trainer) or region[0x7c]!=saved.gender:
        raise ValueError('Live-Team gehört nicht zu diesem Spieler.')
    maximum,count=struct.unpack_from('<II',region,0x90)
    if maximum!=6 or count>6:raise ValueError('Ungültige Teamgröße.')
    party=[]
    for i in range(count):
        raw=bytearray(region[0x98+i*236:0x98+(i+1)*236])
        flags=struct.unpack_from('<H',raw,4)[0]
        if flags&~3:raise ValueError('Pokémon wird gerade verändert.')
        # RAM can contain temporarily decrypted structures. Re-encrypt our COPY
        # for the existing checked parser; the game's memory is never changed.
        if flags&2:_crypt(raw,8,136,struct.unpack_from('<H',raw,6)[0])
        if flags&1:_crypt(raw,136,236,struct.unpack_from('<I',raw,0)[0])
        mon=_pokemon(bytes(raw),True)
        if not mon or not 1<=mon.level<=100 or not 1<=mon.max_hp<=999 or not 0<=mon.hp<=mon.max_hp:
            raise ValueError('Live-Pokémon noch nicht vollständig lesbar.')
        party.append(mon)
    if len({p.uid for p in party})!=len(party):raise ValueError('Doppeltes Live-Pokémon.')
    boxes=[]
    storage_offset,storage_size=entries[41]
    # PCStorage contains 18 boxes of 0x1000 bytes. Reading this live copy is
    # what makes a catch visible even when a full party sends it straight to
    # the PC and the player has not saved yet.
    if storage_size>=0x12000:
        for box in range(18):
            base=storage_offset+box*0x1000
            for slot in range(30):
                start=base+slot*136
                raw=bytearray(region[start:start+136])
                if len(raw)!=136:raise ValueError('Unvollständige Live-Boxdaten.')
                if not any(raw) or raw==b'\xff'*136:continue
                flags=struct.unpack_from('<H',raw,4)[0]
                if flags&~3:raise ValueError('Box-Pokémon wird gerade verändert.')
                if flags&2:_crypt(raw,8,136,struct.unpack_from('<H',raw,6)[0])
                mon=_pokemon(bytes(raw),False)
                if not mon:raise ValueError('Live-Boxdaten noch nicht vollständig lesbar.')
                boxes.append(mon)
    if len({p.uid for p in boxes})!=len(boxes):raise ValueError('Doppeltes Live-Box-Pokémon.')
    known={p.uid for p in party}
    owned=party+[p for p in boxes if p.uid not in known]
    known.update(p.uid for p in owned)
    owned.extend(p for p in saved.owned if p.uid not in known)
    return SaveState(saved.trainer,saved.gender,party,owned)

def read_team(path:Path,saved:SaveState):
    if not -2<=time.time()-path.stat().st_mtime<=60:raise ValueError('Live-Team ist veraltet.')
    return parse_team(path.read_bytes(),saved)
