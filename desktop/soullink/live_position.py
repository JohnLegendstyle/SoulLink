"""Validated, read-only player location snapshots from the emulator."""
import struct
import time
from pathlib import Path

MAGIC=b'SLPOS01\0'

def parse_position(data:bytes, captured_at:int):
    if len(data)!=28 or data[:8]!=MAGIC:
        raise ValueError('Unbekannte Live-Position.')
    map_id,x,y,direction,sequence=struct.unpack_from('<iiiii',data,8)
    if not 0<=map_id<=1000 or not 0<=x<=100000 or not 0<=y<=100000 or not 0<=direction<=3 or sequence<0:
        raise ValueError('Ungültige Live-Position.')
    return {'mapId':map_id,'x':x,'y':y,'direction':direction,'capturedAt':captured_at}

def read_position(path:Path):
    modified=path.stat().st_mtime
    if not -2<=time.time()-modified<=10:
        raise ValueError('Live-Position ist veraltet.')
    return parse_position(path.read_bytes(),int(modified*1000))
