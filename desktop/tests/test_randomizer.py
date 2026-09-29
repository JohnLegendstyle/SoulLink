import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from soullink.randomizer import PlayerPack, choose_starter


class RandomizerTests(unittest.TestCase):
    def test_launcher_starter_choice_is_remembered_without_changing_cloud_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            rom = root / 'SoulSilver_Optimus.nds'
            save = root / 'SoulSilver_Optimus.sav'
            rom.write_bytes(b'jedi-randomized-rom')
            save.write_bytes(b'pre-starter')
            original_identity = 'a' * 64
            identity_path = rom.with_suffix('.graphics-identity.json')
            identity_path.write_text(json.dumps({
                'format': 1,
                'original': original_identity,
                'current': hashlib.sha256(rom.read_bytes()).hexdigest(),
            }))
            manifest = root / 'runde.json'
            manifest.write_text(json.dumps({
                'format': 1,
                'players': [{'player': 'Optimus', 'selectedStarter': None}],
            }))
            pack = PlayerPack(
                'Optimus', 'Anakin', rom, save, 1,
                [{'species': 1, 'name': 'Bisasam'}, {'species': 4, 'name': 'Glumanda'},
                 {'species': 7, 'name': 'Schiggy'}],
            )

            def run(command, **_kwargs):
                Path(command[-2]).write_bytes(b'rom-with-selected-starter')
                return SimpleNamespace(returncode=0, stdout='', stderr='')

            with patch('soullink.randomizer.read_save', return_value=SimpleNamespace(owned=[])), \
                    patch('soullink.randomizer.java_binary', return_value='java'), \
                    patch('soullink.randomizer.classpath', return_value='classes'), \
                    patch('soullink.randomizer.subprocess.run', side_effect=run):
                selected = choose_starter(pack, 1, manifest)

            self.assertEqual(selected.selected_starter, 1)
            self.assertEqual(rom.read_bytes(), b'rom-with-selected-starter')
            self.assertEqual(json.loads(manifest.read_text())['players'][0]['selectedStarter'], 1)
            identity = json.loads(identity_path.read_text())
            self.assertEqual(identity['original'], original_identity)
            self.assertEqual(identity['current'], hashlib.sha256(rom.read_bytes()).hexdigest())
            self.assertEqual(rom.with_suffix('.starter-options.nds').read_bytes(), b'jedi-randomized-rom')
            self.assertFalse(rom.with_suffix('.starter-rollback.nds').exists())

    def test_started_round_cannot_change_starter(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            rom = root / 'game.nds'; rom.touch()
            save = root / 'game.sav'; save.touch()
            manifest = root / 'runde.json'; manifest.write_text('{}')
            pack = PlayerPack('Bee', 'Obi-Wan', rom, save, 1, [{'species': 1, 'name': 'Bisasam'}])
            with patch('soullink.randomizer.read_save', return_value=SimpleNamespace(owned=[object()])):
                with self.assertRaises(ValueError):
                    choose_starter(pack, 0, manifest)


if __name__ == '__main__':
    unittest.main()
