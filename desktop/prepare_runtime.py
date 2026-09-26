from __future__ import annotations

import hashlib
import gzip
import shutil
import subprocess
import urllib.request
import zipfile
import platform
from pathlib import Path


VERSION = "4.6.1"
URL = "https://github.com/Ajarmar/universal-pokemon-randomizer-zx/releases/download/v4.6.1/PokeRandoZX-v4_6_1.zip"
ZIP_SHA256 = "26051fe8a6665ea0582dfcd4d1c3e4889da42a2f731f5fc530fff0cb691a43fd"


def main() -> None:
    root = Path(__file__).resolve().parent / "randomizer"
    archive = root / "PokeRandoZX.zip"
    root.mkdir(parents=True, exist_ok=True)
    for checkpoint in (root / 'checkpoints').glob('*.sav.gz'):
        data = gzip.decompress(checkpoint.read_bytes())
        if len(data) != 0x80000:
            raise ValueError('Ungültiger Checkpoint: ' + checkpoint.name)
        checkpoint.with_suffix('').write_bytes(data)
    if not archive.is_file():
        urllib.request.urlretrieve(URL, archive)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest != ZIP_SHA256:
        raise RuntimeError(f"Unexpected Randomizer ZIP checksum: {digest}")
    with zipfile.ZipFile(archive) as zipped:
        with zipped.open("PokeRandoZX.jar") as source, (root / "PokeRandoZX.jar").open("wb") as target:
            shutil.copyfileobj(source, target)
    classes = root / "classes"
    classes.mkdir(exist_ok=True)
    subprocess.run([
        "javac", "--release", "17", "-encoding", "UTF-8", "-cp", str(root / "PokeRandoZX.jar"), "-d", str(classes),
        str(root / "StarterRandomizer.java"),
    ], check=True)
    jre = root / 'jre'
    if not jre.exists():
        subprocess.run(['jlink','--add-modules','java.base,java.desktop,java.logging,java.prefs,java.xml,java.management,jdk.unsupported',
                        '--strip-debug','--no-header-files','--no-man-pages','--output',str(jre)], check=True)
    vendor = root.parent / 'vendor'
    vendor.mkdir(exist_ok=True)
    windows = platform.system() == 'Windows'
    asset = 'melonDS-1.1-windows-x86_64.zip' if windows else 'melonDS-1.1-macOS-universal.zip'
    expected = '9f3f8a244103be20b5b657af5b0ed1b2a66bb20a7181476a6d294c9a53d4f8c8' if windows else '79843a5e5cab93188bd11942bff5440b9505ee91c6f526f7e90c22e3cff6718d'
    archive = vendor / asset
    if not archive.exists(): urllib.request.urlretrieve('https://github.com/melonDS-emu/melonDS/releases/download/1.1/' + asset,archive)
    if hashlib.sha256(archive.read_bytes()).hexdigest() != expected: raise ValueError('melonDS-Prüfsumme stimmt nicht.')
    emulator = vendor / 'Emulator'
    emulator.mkdir(exist_ok=True)
    if windows:
        with zipfile.ZipFile(archive) as z: z.extractall(emulator)
    else:
        subprocess.run(['ditto','-x','-k',str(archive),str(emulator)],check=True)
    sources = vendor / 'Quelltexte'
    sources.mkdir(exist_ok=True)
    for filename,url in (
        ('melonDS-1.1.zip','https://github.com/melonDS-emu/melonDS/archive/refs/tags/1.1.zip'),
        ('Randomizer-ZX-4.6.1.zip','https://github.com/Ajarmar/universal-pokemon-randomizer-zx/archive/refs/tags/v4.6.1.zip')):
        if not (sources / filename).exists(): urllib.request.urlretrieve(url,sources / filename)


if __name__ == "__main__":
    main()
