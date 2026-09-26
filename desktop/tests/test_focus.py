import tempfile
import unittest
from pathlib import Path
from soullink.melonds import DEFAULT_KEYS, write_config, read_runtime_settings, qt_key, copy_emulator


class FocusTests(unittest.TestCase):
    def test_portable_update_uses_new_bundled_emulator(self):
        from soullink.melonds import preferred_emulator
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);old=root/'old'/'Emulator'/'melonDS.exe';new=root/'new'/'Emulator'/'melonDS.exe'
            old.parent.mkdir(parents=True);old.touch();new.parent.mkdir(parents=True);new.touch()
            self.assertEqual(preferred_emulator(str(old),new),str(new))
            custom=root/'custom.exe';custom.touch()
            self.assertEqual(preferred_emulator(str(custom),new),str(custom))
            self.assertEqual(preferred_emulator('',new),str(new))
    def test_both_native_title_paths_use_jedi_display_names(self):
        root=Path(__file__).resolve().parents[1]/'focus'
        for name in ('FocusWindow.inc','apply_focus.py'):
            lines=[line for line in (root/name).read_text().splitlines() if 'setWindowTitle("Soul Link' in line]
            self.assertEqual(len(lines),1)
            self.assertIn('QString("Anakin")',lines[0])
            self.assertIn('QString("Obi-Wan")',lines[0])
        text=(root/'FocusWindow.inc').read_text()
        self.assertIn('button(name=="Optimus"?QString("Anakin"):QString("Obi-Wan")',text)

    def test_streaming_can_continue_when_browser_has_focus(self):
        import tomllib
        with tempfile.TemporaryDirectory() as temp:
            config=write_config(Path(temp)/'melonDS.exe',scale=4,fps=120,volume_percent=80,keys=DEFAULT_KEYS,save_directory=Path(temp)/'saves',pause_lost_focus=False)
            self.assertFalse(tomllib.loads(config.read_text())['PauseLostFocus'])
    def test_graphics_settings_roundtrip(self):
        with tempfile.TemporaryDirectory() as temp:
            exe=Path(temp)/'melonDS.exe'
            for layout in ('focus','horizontal','vertical'):
                for smooth in (False,True):
                    write_config(exe,scale=8,fps=120,volume_percent=75,keys=DEFAULT_KEYS,
                                 save_directory=Path(temp)/'saves',pixel_filter=smooth,
                                 integer_scaling=True,screen_layout=layout)
                    values=read_runtime_settings(exe)
                    self.assertEqual(values['scale'],8)
                    self.assertEqual(values['fps'],120)
                    self.assertEqual(values['volume'],75)
                    self.assertEqual(values['pixel_filter'],smooth)
                    self.assertTrue(values['integer_scaling'])
                    self.assertEqual(values['screen_layout'],layout)
                    for key,value in DEFAULT_KEYS.items():
                        self.assertEqual(qt_key(values['keys'][key]),qt_key(value))

    def test_native_special_keys_are_not_lost(self):
        with tempfile.TemporaryDirectory() as temp:
            exe=Path(temp)/'melonDS.exe'
            keys={**DEFAULT_KEYS,'A':'QT:16777268'}
            write_config(exe,scale=4,fps=0,volume_percent=0,keys=keys,save_directory=Path(temp))
            values=read_runtime_settings(exe)
            self.assertEqual(qt_key(values['keys']['A']),16777268)
            self.assertEqual(values['fps'],0)
        with self.assertRaises(ValueError): qt_key('QT:999999999999')

    def test_layout_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                write_config(Path(temp)/'test.exe',scale=4,fps=60,volume_percent=80,
                             keys=DEFAULT_KEYS,save_directory=Path(temp),screen_layout='invalid')

    def test_new_binary_gets_new_isolated_directory(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);source=root/'source';source.mkdir()
            executable=source/'melonDS.exe';executable.write_bytes(b'old binary')
            with patch('soullink.melonds.platform.system',return_value='Windows'):
                first=copy_emulator(executable,root/'copies')
                executable.write_bytes(b'new binary')
                second=copy_emulator(executable,root/'copies')
            self.assertNotEqual(first,second)
            self.assertEqual(first.read_bytes(),b'old binary')
            self.assertEqual(second.read_bytes(),b'new binary')


if __name__=='__main__': unittest.main()
