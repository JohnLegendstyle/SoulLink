import binascii
import json
import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from soullink.checkpoint import named_checkpoint
from soullink.save_reader import read_save, _active, _text, _pokemon, GENERAL_SIZE, PARTITION_SIZE
from soullink.randomizer import create_round, load_round
from soullink.melonds import DEFAULT_KEYS, qt_key, write_config

CHECKPOINTS = Path(__file__).resolve().parents[1] / 'randomizer' / 'checkpoints'


class CoreTests(unittest.TestCase):
    def test_synthetic_party_and_box_decryption(self):
        # Entirely synthetic data, no user-save bytes or real trainer IDs.
        # Non-self-inverse block order 17 catches reversed permutation tables.
        pid=(17<<13)|0x42
        plain=bytearray(236)
        struct.pack_into('<I',plain,0,pid)
        struct.pack_into('<H',plain,8,63)
        struct.pack_into('<I',plain,0x0C,0x12345678)
        struct.pack_into('<5H',plain,0x48,0x12B,0x12C,0x13C,0x12B,0xFFFF)
        plain[0x8C]=5
        struct.pack_into('<HH',plain,0x8E,19,19)
        checksum=sum(struct.unpack('<64H',plain[8:136]))&0xFFFF
        struct.pack_into('<H',plain,6,checksum)
        blocks=[plain[8+i*32:40+i*32] for i in range(4)]
        raw=bytearray(plain)
        raw[8:136]=blocks[2]+blocks[3]+blocks[1]+blocks[0]
        for start,end,seed in ((8,136,checksum),(136,236,pid)):
            for offset in range(start,end,2):
                seed=(seed*0x41C64E6D+0x6073)&0xFFFFFFFF
                struct.pack_into('<H',raw,offset,struct.unpack_from('<H',raw,offset)[0]^(seed>>16))
        party=_pokemon(raw,True)
        self.assertEqual((party.species,party.nickname,party.level,party.hp,party.max_hp),(63,'ABRA',5,19,19))
        boxed=_pokemon(raw[:136],False)
        self.assertEqual((boxed.species,boxed.nickname,boxed.uid),(63,'ABRA',f'{pid:08x}-12345678'))
        corrupted=bytearray(raw); corrupted[30]^=1
        self.assertIsNone(_pokemon(corrupted,True))

    def test_packaged_checkpoints_are_valid_and_pre_starter(self):
        for trainer in ('Optimus','Bee'):
            state = read_save(CHECKPOINTS / (trainer + '.sav'))
            self.assertEqual(state.trainer,trainer)
            self.assertEqual(state.gender,0)
            self.assertEqual(state.party,[])
            self.assertEqual(state.owned,[])

    def test_renaming_preserves_game_state_and_valid_crc(self):
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'Bee.sav'
            named_checkpoint(CHECKPOINTS/'Optimus.sav',target,'Bee')
            self.assertEqual(read_save(target).trainer,'Bee')
            original=(CHECKPOINTS/'Optimus.sav').read_bytes()
            modified=target.read_bytes()
            allowed=set()
            for base in (0,PARTITION_SIZE):
                allowed.update(range(base+0x64,base+0x74))
                allowed.update((base+0x7C,base+GENERAL_SIZE-2,base+GENERAL_SIZE-1))
            self.assertTrue(all(a==b or i in allowed for i,(a,b) in enumerate(zip(original,modified))))

    def test_invalid_save_does_not_publish_corrupt_data(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'bad.sav'
            path.write_bytes(b'\xff'*0x80000)
            with self.assertRaises(ValueError): read_save(path)
            path.write_bytes(b'\x00'*0x80000)
            with self.assertRaises(ValueError): read_save(path)

    def test_bad_rom_is_rejected_before_creating_a_round(self):
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory)
            rom=base/'wrong.nds'; rom.write_bytes(b'POKEMON SS\0\0IPGE')
            with self.assertRaises(ValueError): create_round(rom,base/'rounds',CHECKPOINTS)
            self.assertFalse((base/'rounds').exists())

    def test_round_manifest_cannot_escape_its_folder(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'runde.json'
            path.write_text(json.dumps({'format':1,'players':[{'player':'Optimus','trainer':'Optimus','rom':'../outside.nds','save':'../outside.sav','seed':1,'starters':[]}]}))
            with self.assertRaises(ValueError): load_round(path)

    def test_speed_profiles_do_not_keep_audio_vsync_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory)
            for fps in (60,90,120,0):
                config=write_config(base/'melonDS.exe',scale=4,fps=fps,volume_percent=80,keys=DEFAULT_KEYS,save_directory=base/'saves')
                import tomllib
                settings=tomllib.loads(config.read_text())
                self.assertEqual(settings['LimitFPS'],fps!=0)
                self.assertEqual(settings['AudioSync'],fps==60)
                self.assertEqual(settings['Screen']['VSync'],fps==60)
                self.assertEqual(settings['Instance0']['Audio']['Volume'],205)
                self.assertEqual(settings['Instance0']['Keyboard']['Left'],0x1000012)
        with self.assertRaises(ValueError): qt_key('not a key')

if __name__ == '__main__': unittest.main()
