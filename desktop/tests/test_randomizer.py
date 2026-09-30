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

    def test_custom_starter_is_saved_as_fourth_choice(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            rom = root / 'SoulSilver_Bee.nds'
            save = root / 'SoulSilver_Bee.sav'
            rom.write_bytes(b'randomized-adventure')
            save.write_bytes(b'pre-starter')
            manifest = root / 'runde.json'
            manifest.write_text(json.dumps({
                'format': 1,
                'players': [{'player': 'Bee', 'selectedStarter': None}],
            }))
            catalog = [
                {'species': 1, 'name': 'Bisasam'},
                {'species': 25, 'name': 'Pikachu'},
            ]
            pack = PlayerPack(
                'Bee', 'Obi-Wan', rom, save, 2,
                [{'species': 145, 'name': 'Zapdos'}, {'species': 249, 'name': 'Lugia'},
                 {'species': 340, 'name': 'Welsar'}],
                catalog=catalog,
            )

            def run(command, **_kwargs):
                self.assertEqual(command[-1], '25')
                Path(command[-2]).write_bytes(b'randomized-adventure-with-pikachu-in-middle')
                return SimpleNamespace(returncode=0, stdout='', stderr='')

            with patch('soullink.randomizer.read_save', return_value=SimpleNamespace(owned=[])), \
                    patch('soullink.randomizer.java_binary', return_value='java'), \
                    patch('soullink.randomizer.classpath', return_value='classes'), \
                    patch('soullink.randomizer.subprocess.run', side_effect=run):
                selected = choose_starter(pack, 3, manifest, custom_species=25)

            data = json.loads(manifest.read_text())['players'][0]
            self.assertEqual(selected.selected_starter, 3)
            self.assertEqual(selected.custom_starter, {'species': 25, 'name': 'Pikachu'})
            self.assertEqual(data['selectedStarter'], 3)
            self.assertEqual(data['customStarter'], {'species': 25, 'name': 'Pikachu'})
            self.assertEqual(rom.read_bytes(), b'randomized-adventure-with-pikachu-in-middle')

    def test_java_adapter_preserves_two_distinct_other_starters_and_adventure(self):
        source = (Path(__file__).parents[1] / 'randomizer' / 'StarterRandomizer.java').read_text()
        self.assertIn('List.of(sides.get(0), chosen, sides.get(1))', source)
        self.assertNotIn('List.of(chosen, chosen, chosen)', source)
        self.assertIn('new Randomizer(settings, handler, bundle, false).randomize', source)
        self.assertIn('wildSaved', source)
        self.assertIn('trainersSaved', source)

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
