import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from soullink.skins import load_skin, apply_skin, patch_rom_bytes, TARGETS


class SkinTests(unittest.TestCase):
    def test_both_skins_have_four_directions_and_transparency(self):
        for player in ('Optimus','Bee'):
            skin = load_skin(player)
            self.assertEqual(len(skin['frames']),16)
            for row in range(4):
                self.assertEqual(skin['frames'][row*4],skin['frames'][row*4+2])
                self.assertTrue(any(v==0 for v in skin['frames'][row*4]))
            self.assertEqual(len({skin['frames'][i*4] for i in range(4)}),4)
        self.assertNotEqual(load_skin('Optimus')['palette'],load_skin('Bee')['palette'])

    def test_unknown_player_is_rejected(self):
        with self.assertRaises(ValueError): load_skin('../invalid')

    def test_backup_is_retained_and_save_never_modified(self):
        with tempfile.TemporaryDirectory() as directory:
            rom=Path(directory)/'game.nds'; rom.write_bytes(b'original')
            save=rom.with_suffix('.sav'); save.write_bytes(b'keep my progress')
            with patch('soullink.skins.patch_rom_bytes',return_value=b'new graphics'):
                self.assertTrue(apply_skin(rom,'Bee'))
                self.assertFalse(apply_skin(rom,'Bee'))
            self.assertEqual(rom.with_suffix('.pre-transformers.nds').read_bytes(),b'original')
            self.assertEqual(save.read_bytes(),b'keep my progress')

    def test_validation_failure_does_not_touch_files(self):
        with tempfile.TemporaryDirectory() as directory:
            rom=Path(directory)/'game.nds'; rom.write_bytes(b'original')
            with patch('soullink.skins.patch_rom_bytes',side_effect=ValueError('invalid')):
                with self.assertRaises(ValueError): apply_skin(rom,'Bee')
            self.assertEqual(rom.read_bytes(),b'original')
            self.assertEqual(list(Path(directory).iterdir()),[rom])

    @unittest.skipUnless(importlib.util.find_spec('ndspy'), 'ndspy installed in packaging step')
    def test_synthetic_rom_roundtrip_idempotence_and_file_isolation(self):
        # Generated container structures only: no commercial game or save bytes.
        from ndspy.rom import NintendoDSRom
        from ndspy.fnt import Folder
        from ndspy.narc import NARC
        from ndspy.texture import NSBTX, Texture, Palette
        narc=NARC(); narc.files=[b'untouched NPC']*214
        for index,prefix in TARGETS.items():
            btx=NSBTX()
            btx.textures=[(f'{prefix}.{i+1}',Texture(0,0,0x2d20,0,bytes([i%256])*512,b'')) for i in range(32)]
            btx.palettes=[('skin',Palette(0,0,0,bytes(32)))]
            narc.files[index]=btx.save()
        rom=NintendoDSRom(); rom.name=b'POKEMON SS';rom.idCode=b'IPGD'
        rom.filenames=Folder(folders=[('a',Folder(folders=[('0',Folder(folders=[('8',Folder(files=['1']))]))]))])
        rom.files=[narc.save()]
        original=bytes(rom.save())
        for player in ('Optimus','Bee'):
            patched=patch_rom_bytes(original,player)
            self.assertEqual(len(patched),len(original))
            self.assertEqual(patch_rom_bytes(patched,player),patched)
            output=NARC(NintendoDSRom(patched).files[0])
            for i,entry in enumerate(narc.files):
                if i not in TARGETS: self.assertEqual(output.files[i],entry)
            for index in TARGETS:
                skin=load_skin(player)
                for name,texture in NSBTX(output.files[index]).textures:
                    self.assertEqual(texture.data1,skin['frames'][(int(name.rsplit('.',1)[1])-1)%16])


if __name__=='__main__': unittest.main()
