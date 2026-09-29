# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import sys

root = Path(SPECPATH)
datas = [
    (str(root / "randomizer" / "PokeRandoZX.jar"), "randomizer"),
    (str(root / "randomizer" / "classes"), "randomizer/classes"),
    (str(root / "randomizer" / "checkpoints"), "randomizer/checkpoints"),
    (str(root / "assets" / "skins" / "optimus-prime.json"), "assets/skins"),
    (str(root / "assets" / "skins" / "bumblebee.json"), "assets/skins"),
]
datas += [(str(file),'assets/jedi') for file in (root/'assets'/'jedi').glob('*.json')]

a = Analysis([str(root / "run.py")], pathex=[str(root)], binaries=[], datas=datas,
             hiddenimports=[], hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="SoulLink", debug=False,
          bootloader_ignore_signals=False, strip=False, upx=True, console=False,
          disable_windowed_traceback=False, argv_emulation=False,
          target_arch=None, codesign_identity=None, entitlements_file=None)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='SoulLink')
if sys.platform == 'darwin':
    app = BUNDLE(coll, name='SoulLink.app', bundle_identifier='de.soullink.desktop',
                 info_plist={'CFBundleShortVersionString':'0.14.4','NSHighResolutionCapable':True})
