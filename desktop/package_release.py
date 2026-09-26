"""Build a portable folder with the app, emulator, Java and license/source notices."""
from pathlib import Path
import shutil
import platform
import subprocess

root = Path(__file__).resolve().parent
windows = platform.system() == 'Windows'
label = 'Windows-x64' if windows else 'macOS-' + platform.machine()
release = root / 'release'
release.mkdir(exist_ok=True)
folder = release / ('SoulLink-' + label)
if folder.exists(): raise RuntimeError('Release-Ordner existiert bereits. Für einen Neubau einen frischen Build-Ordner verwenden.')
folder.mkdir()
if windows:
    shutil.copytree(root / 'dist' / 'SoulLink',folder,dirs_exist_ok=True)
else:
    shutil.copytree(root / 'dist' / 'SoulLink.app',folder / 'SoulLink.app',symlinks=True)
shutil.copytree(root / 'randomizer' / 'jre',folder / 'Runtime',symlinks=True)
emulator = root / 'vendor' / 'Emulator'
source = next(emulator.rglob('melonDS.exe')).parent if windows else next(emulator.rglob('melonDS.app')).parent
shutil.copytree(source,folder / 'Emulator',symlinks=True)
shutil.copytree(root / 'vendor' / 'Quelltexte',folder / 'Quelltexte')
for filename in ('SPIELSTART.md','THIRD_PARTY_NOTICES.md','LICENSE'):
    shutil.copy2(root.parent / filename,folder / filename)
archive = release / (folder.name + '.zip')
executable=folder/'SoulLink.exe' if windows else folder/'SoulLink.app'/'Contents'/'MacOS'/'SoulLink'
subprocess.run([str(executable),'--self-test'],check=True,timeout=60)
if windows:
    shutil.make_archive(str(archive.with_suffix('')),'zip',release,folder.name)
else:
    subprocess.run(['ditto','-c','-k','--sequesterRsrc','--keepParent',str(folder),str(archive)],check=True)
print(archive)
