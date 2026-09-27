import struct,tempfile,time,unittest,os
from pathlib import Path
from soullink.live_team import parse_team,read_team,REGION_SIZE
from soullink.identity import name_bytes
from soullink.save_reader import SaveState,_crypt

def pokemon_raw(size=236,flags=0,hp=19,pid=0x42):
    raw=bytearray(size);struct.pack_into('<IHH',raw,0,pid,flags,0)
    struct.pack_into('<HI',raw,8,63,0)
    struct.pack_into('<I',raw,0x0c,0x12345678)
    if size>136:
        raw[0x8c]=5;struct.pack_into('<HH',raw,0x8e,hp,19)
    checksum=sum(struct.unpack('<64H',raw[8:136]))&65535;struct.pack_into('<H',raw,6,checksum)
    if not flags&2:_crypt(raw,8,136,checksum)
    if size>136 and not flags&1:_crypt(raw,136,size,pid)
    return raw

def snapshot(flags=0,hp=19,boxed=False):
    region=bytearray(REGION_SIZE);region[0x64:0x74]=name_bytes('Anakin')
    struct.pack_into('<II',region,0x90,6,1)
    region[0x98:0x98+236]=pokemon_raw(flags=flags,hp=hp)
    headers=bytearray(42*16);offset=0
    for i in range(42):
        size=0x60 if i==0 else 0x30 if i==1 else 8+6*236 if i==2 else 0x122fc if i==41 and boxed else 4
        struct.pack_into('<IIIHH',headers,i*16,i,size,offset,0,0);offset+=size
    if boxed:
        storage=struct.unpack_from('<I',headers,41*16+8)[0]
        region[storage:storage+136]=pokemon_raw(size=136,pid=0x99)
    return b'SLTEAM01'+region+headers

class LiveTeamTests(unittest.TestCase):
    saved=SaveState('Anakin',0,[],[])
    def test_unsaved_party_and_hp_without_save_changes(self):
        for flags in range(4):
            raw=snapshot(flags);before=bytes(raw)
            state=parse_team(raw,self.saved)
            self.assertEqual((len(state.party),state.party[0].species,state.party[0].hp),(1,63,19))
            self.assertEqual(raw,before);self.assertEqual(self.saved.party,[])
        self.assertEqual(parse_team(snapshot(hp=0),self.saved).party[0].hp,0)
    def test_unsaved_box_catch_is_included_without_game_save(self):
        state=parse_team(snapshot(boxed=True),self.saved)
        self.assertEqual(len(state.party),1)
        self.assertEqual([(p.species,p.level) for p in state.owned],[(63,5),(63,None)])
    def test_rejects_wrong_player_corruption_and_bad_stats(self):
        with self.assertRaises(ValueError):parse_team(snapshot(),SaveState('Obi-Wan',0,[],[]))
        for offset in (0,8+0x98+20,8+REGION_SIZE+32):
            data=bytearray(snapshot());data[offset]^=255
            with self.assertRaises(ValueError):parse_team(bytes(data),self.saved)
        with self.assertRaises(ValueError):parse_team(snapshot(hp=20),self.saved)
        with self.assertRaises(ValueError):parse_team(snapshot(flags=4),self.saved)
    def test_stale_snapshot_never_overwrites_saved_team(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'test.team';path.write_bytes(snapshot())
            self.assertEqual(len(read_team(path,self.saved).party),1)
            os.utime(path,(time.time()-61,)*2)
            with self.assertRaises(ValueError):read_team(path,self.saved)
