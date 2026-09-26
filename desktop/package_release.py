"""Build a portable folder with the app, emulator, Java and license/source notices."""
from pathlib import Path
import shutil
import platform
import subprocess
import zipfile
import sys

root = Path(__file__).resolve().parent
subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=root,check=True)
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
emulator = root / 'vendor' / 'FocusEmulator'
source = next(emulator.rglob('melonDS.exe')).parent if windows else next(emulator.rglob('melonDS.app')).parent
shutil.copytree(source,folder / 'Emulator',symlinks=True)
shutil.copytree(root / 'vendor' / 'Quelltexte',folder / 'Quelltexte')
# Ship the matching source of the GPL Python library alongside frozen binaries.
subprocess.run([sys.executable,'-m','pip','download','--no-deps',
                '--no-binary=:all:','ndspy==4.2.0',
                '--dest',str(folder / 'Quelltexte')],check=True)
for filename in ('SPIELSTART.md','THIRD_PARTY_NOTICES.md','LICENSE'):
    shutil.copy2(root.parent / filename,folder / filename)
archive = release / (folder.name + '.zip')
executable=folder/'SoulLink.exe' if windows else folder/'SoulLink.app'/'Contents'/'MacOS'/'SoulLink'
try:
    subprocess.run([str(executable),'--self-test'],check=True,timeout=60)
except subprocess.SubprocessError:
    report=Path('soullink-self-test-error.txt')
    if report.exists(): print(report.read_text(),flush=True)
    raise
if windows:
    shutil.make_archive(str(archive.with_suffix('')),'zip',release,folder.name)
else:
    subprocess.run(['ditto','-c','-k','--sequesterRsrc','--keepParent',str(folder),str(archive)],check=True)
print(archive)
if not windows:
    with zipfile.ZipFile(release / 'SoulLink-Startspielstaende.zip','w',zipfile.ZIP_DEFLATED) as zipped:
        for name in ('Optimus','Bee'):
            zipped.write(root/'randomizer'/'checkpoints'/(name+'.sav'),name+'/'+name+'.sav')
        zipped.write(root.parent/'SPIELSTART.md','SPIELSTART.md')
