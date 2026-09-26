"""Player display identities; legacy storage keys remain stable."""
import binascii
import struct
from pathlib import Path
from .save_reader import parse_save,GENERAL_SIZE,PARTITION_SIZE

NAMES={'Optimus':'Anakin','Bee':'Obi-Wan'}
ACCOUNTS={'John':'Optimus','Eddie':'Bee'}

def allowed_names(account):
    key=ACCOUNTS[account]
    return (key,NAMES[key])

def name_bytes(name):
    if not 1<=len(name)<=7 or any(not('A'<=c<='Z' or 'a'<=c<='z' or c=='-') for c in name):
        raise ValueError('Trainername: 1–7 Buchstaben oder Bindestrich.')
    chars=[0x1be if c=='-' else 0x12b+ord(c)-65 if c.isupper() else 0x145+ord(c)-97 for c in name]
    return struct.pack('<8H',*(chars+[0xffff]+[0]*(7-len(chars))))

def renamed_data(original,player):
    state=parse_save(original);name=NAMES[player]
    if state.trainer==name:return original
    if state.trainer!=player:raise ValueError('Dieser Spielstand gehört zu einem anderen Spieler.')
    # Current user saves are pre-starter. Never silently change OT ownership of
    # an established team: a later migration needs a separately tested OT pass.
    if state.owned:raise ValueError('Diese alte Runde enthält bereits Pokémon. Die Namensänderung wurde sicherheitshalber nicht durchgeführt; Spielstand unverändert.')
    data=bytearray(original)
    for base in (0,PARTITION_SIZE):
        block=data[base:base+GENERAL_SIZE]
        if binascii.crc_hqx(block[:-16],0xffff)!=struct.unpack_from('<H',block,GENERAL_SIZE-2)[0]:continue
        data[base+0x64:base+0x74]=name_bytes(name)
        struct.pack_into('<H',data,base+GENERAL_SIZE-2,binascii.crc_hqx(data[base:base+GENERAL_SIZE-16],0xffff))
    if parse_save(data).trainer!=name:raise ValueError('Namensprüfung fehlgeschlagen.')
    return bytes(data)

def rename_save(save:Path,player):
    from .cloud import atomic_write
    original=save.read_bytes();changed=renamed_data(original,player)
    if original==changed:return False
    backup=save.with_suffix('.pre-jedi-name.sav')
    try:
        with backup.open('xb') as f:f.write(original)
    except FileExistsError:pass
    atomic_write(save,changed)
    return True
