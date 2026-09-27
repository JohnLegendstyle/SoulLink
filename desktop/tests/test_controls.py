import os
import tempfile
import unittest
from pathlib import Path
from soullink.controls import load_profile,save_profile,read_native,key_label
from soullink.melonds import write_config,qt_key,DEFAULT_KEYS

class ControlTests(unittest.TestCase):
    def test_full_profile_survives_new_binary_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);old=root/'Emulator'/'Optimus'/'build-old'/'portable'/'melonDS.toml'
            old.parent.mkdir(parents=True)
            old.write_text('[Instance0]\nJoystickID=2\n[Instance0.Keyboard]\nA=75\nB=-1\nL=-2130706400\nHK_Pause=67108944\n[Instance0.Joystick]\nA=3\nHK_Reset=7\n')
            profile=load_profile(root,'Optimus');save_profile(root,'Optimus',profile)
            exe=root/'Emulator'/'Optimus'/'build-new'/'melonDS.exe'
            keys={**DEFAULT_KEYS,**{key:key_label(value) for key,value in profile['Keyboard'].items() if key in DEFAULT_KEYS}}
            destination=write_config(exe,scale=4,fps=120,volume_percent=80,keys=keys,save_directory=root/'saves',input_profile=profile)
            restored=read_native(destination)
            for table in ('Keyboard','Joystick'):
                for key,value in profile[table].items():self.assertEqual(restored[table][key],value)
            self.assertEqual(restored['JoystickID'],2)
            self.assertEqual(load_profile(root,'Bee')['Keyboard'],{})
            self.assertTrue(old.is_file())

    def test_launcher_edits_take_precedence_and_backup_recovers(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);profile={'Keyboard':{'A':75,'HK_Pause':80},'Joystick':{'B':4},'JoystickID':1}
            save_profile(root,'Bee',profile)
            profile['Keyboard']['A']=77;save_profile(root,'Bee',profile)
            path=root/'Controls'/'Bee.json';path.write_text('broken')
            self.assertEqual(load_profile(root,'Bee')['Keyboard']['A'],75)
            dest=write_config(root/'new'/'melonDS.exe',scale=4,fps=60,volume_percent=80,keys={'A':'J'},save_directory=root,input_profile=profile)
            result=read_native(dest)
            self.assertEqual(result['Keyboard']['A'],ord('J'))
            self.assertEqual(result['Keyboard']['HK_Pause'],80)
            self.assertEqual(result['Joystick']['B'],4)

    def test_latest_native_changes_recover_after_unexpected_launcher_exit(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);save_profile(root,'Optimus',{'Keyboard':{'A':65}})
            native=root/'Emulator'/'Optimus'/'build-one'/'portable'/'melonDS.toml';native.parent.mkdir(parents=True)
            native.write_text('[Instance0.Keyboard]\nA=77\n')
            os.utime(native,(2000000000,2000000000))
            self.assertEqual(load_profile(root,'Optimus')['Keyboard']['A'],77)
            # A corrupt newer file cannot erase the last valid mapping.
            native.write_text('broken');self.assertEqual(load_profile(root,'Optimus')['Keyboard']['A'],65)

    def test_disabled_modifier_and_right_hand_keys_round_trip(self):
        for value in (-1,-2130706400,67108944,16777268,65):
            self.assertEqual(qt_key(key_label(value)),value)
        for value in ('QT:2147483648','QT:-2147483649'):
            with self.assertRaises(ValueError):qt_key(value)
