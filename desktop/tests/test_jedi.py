import hashlib
import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from soullink.jedi import (PLAYERS,roster,load_character,assignments,_dp_cipher,
                           _sprite_tiles,_field,_field_frame_index,apply_jedi,rom_identity)

class JediTests(unittest.TestCase):
    def test_names_preserve_both_save_partitions_and_game_state(self):
        from soullink.identity import renamed_data,name_bytes
        from soullink.save_reader import parse_save,GENERAL_SIZE,PARTITION_SIZE
        root=Path(__file__).resolve().parents[1]/'randomizer'/'checkpoints'
        for player,name in (('Optimus','Anakin'),('Bee','Obi-Wan')):
            original=(root/(player+'.sav')).read_bytes()
            renamed=renamed_data(original,player)
            self.assertEqual(parse_save(renamed).trainer,name)
            self.assertEqual(renamed_data(renamed,player),renamed)
            self.assertEqual(parse_save(renamed).party,parse_save(original).party)
            allowed=set()
            for base in (0,PARTITION_SIZE):
                allowed.update(range(base+0x64,base+0x74))
                allowed.update((base+GENERAL_SIZE-2,base+GENERAL_SIZE-1))
            self.assertTrue(all(a==b or i in allowed for i,(a,b) in enumerate(zip(original,renamed))))
        with self.assertRaises(ValueError):name_bytes('TooLongName')

    def test_roster_and_player_identity(self):
        self.assertEqual(PLAYERS,{'Optimus':'anakin-skywalker','Bee':'obi-wan-kenobi'})
        ids={c['id'] for c in roster()}
        self.assertGreaterEqual(len(ids),36)
        for player in PLAYERS:
            battle,world=assignments(player)
            self.assertEqual(set(battle),set(range(129)))
            self.assertEqual(world['hero'],PLAYERS[player])
            self.assertTrue(ids-set(PLAYERS.values())<=set(battle.values()))
            self.assertTrue(ids-set(PLAYERS.values())<=set(world.values()))

    def test_every_character_has_four_views_blades_and_battle_views(self):
        for c in roster():
            data=load_character(c['id'])
            self.assertEqual(len(set(data['frames'])),12)
            for key in ('frames','front','back'):
                for raw in data[key]:
                    pixels=[p for b in raw for p in (b&15,b>>4)]
                    for index in data['bladeIndices']:self.assertIn(index,pixels,c['id'])
                    # New palettes preserve the approved alien artwork exactly.
                    # Check actual occupied head pixels, not a former color index.
                    width=32 if key=='frames' else 80
                    self.assertGreater(sum(bool(pixels[y*width+x]) for y in range(7,17) for x in range(11,21)) if width==32 else sum(bool(v) for v in pixels[:80*50]),25,c['id'])
                    self.assertEqual(raw[-2:],b'\0\0')
            self.assertNotEqual(data['front'],data['back'])

    def test_picture_cipher_roundtrip(self):
        original=bytes((i%256 for i in range(6398)))+bytes(2)
        encoded=_dp_cipher(original)
        words=list(struct.unpack('<3200H',encoded));seed=words[-1]
        for i in range(3199,-1,-1):
            words[i]^=seed&65535;seed=(seed*1103515245+24691)&0xffffffff
        self.assertEqual(struct.pack('<3200H',*words),original)

    def test_field_texture_roundtrip(self):
        try:from ndspy.texture import NSBTX,Texture,Palette
        except ImportError:self.skipTest('ndspy installed in packaging step')
        btx=NSBTX();btx.textures=[(f'hero.{i+1}',Texture(0,0,0x2d20,0,bytes([i])*512,b'')) for i in range(32)]
        btx.palettes=[('skin',Palette(0,0,0,bytes(32)))]
        original=btx.save();skin=load_character(PLAYERS['Optimus'])
        result=_field(original,skin)
        self.assertEqual(len(result),len(original))
        self.assertEqual(_field(result,skin),result)
        for name,t in NSBTX(result).textures:
            self.assertEqual(t.data1,skin['frames'][_field_frame_index(int(name.split('.')[1]))])

    def test_field_direction_banks_match_soulsilver(self):
        # Game banks: back, front, left, right. Approved art: back, front,
        # right, left. Animation phases and the second 16-frame set stay put.
        self.assertEqual([_field_frame_index(i) for i in (1,5,9,13)], [0,4,12,8])
        self.assertEqual([_field_frame_index(i) for i in (17,21,25,29)], [0,4,12,8])
        self.assertEqual([_field_frame_index(i) for i in (10,14)], [13,9])

    def test_vram_cells_pack_tiles_at_original_offsets(self):
        # One generated 8x8 OAM shape, one transfer slot, no game-derived bytes.
        cells=bytearray(94);cells[:4]=b'RECN';cells[16:20]=b'KBEC'
        struct.pack_into('<HHIII',cells,24,1,1,24,0,48)
        struct.pack_into('<HHI',cells,48,1,0,0)
        struct.pack_into('<HHH',cells,64,0,0,0)
        struct.pack_into('<II',cells,72,32,8)
        struct.pack_into('<II',cells,80,0,32)
        frame=bytes([0x21])*3200
        self.assertEqual(_sprite_tiles(cells,[frame,frame],32),bytes([0x21])*32)

    def test_battle_palette_covers_every_animation_bank(self):
        from soullink.jedi import _battle,palette_bytes
        skin=load_character(PLAYERS['Optimus'])
        pixels=b'RGCN'+bytes(76)
        palette=b'RLCN'+bytes(548)
        picture=b'RGCN'+bytes(6444)
        with patch('soullink.jedi._sprite_tiles',return_value=bytes(32)):
            result=_battle((pixels,palette,b'cells',b'animation',picture),skin)
        self.assertEqual(len(result[1]),len(palette))
        for bank in range(16):
            self.assertEqual(result[1][40+bank*32:72+bank*32],palette_bytes(skin))

    def test_graphics_patch_retains_cloud_identity_and_save(self):
        with tempfile.TemporaryDirectory() as directory:
            rom=Path(directory)/'round.nds';rom.write_bytes(b'old graphics')
            save=rom.with_suffix('.sav');save.write_bytes(b'keep progress')
            identity=rom_identity(rom)
            with patch('soullink.jedi.patch_rom_bytes',return_value=(b'jedi graphics',[])):
                self.assertTrue(apply_jedi(rom,'Optimus'))
                self.assertFalse(apply_jedi(rom,'Optimus'))
            self.assertEqual(rom_identity(rom),identity)
            self.assertEqual(rom.with_suffix('.pre-jedi.nds').read_bytes(),b'old graphics')
            self.assertEqual(save.read_bytes(),b'keep progress')
            rom.write_bytes(b'different randomized game')
            self.assertEqual(rom_identity(rom),hashlib.sha256(rom.read_bytes()).hexdigest())

    def test_invalid_patch_does_not_write_anything(self):
        with tempfile.TemporaryDirectory() as directory:
            rom=Path(directory)/'round.nds';rom.write_bytes(b'original')
            with patch('soullink.jedi.patch_rom_bytes',side_effect=ValueError('invalid')):
                with self.assertRaises(ValueError):apply_jedi(rom,'Bee')
            self.assertEqual(list(Path(directory).iterdir()),[rom])
            self.assertEqual(rom.read_bytes(),b'original')

if __name__=='__main__':unittest.main()
