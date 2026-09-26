# Third-party software

SoulLink desktop code and its Java adapter are provided under GNU GPL v3 or later; see LICENSE. No Nintendo ROM, BIOS, firmware dump or copyrighted game media is included in releases.

- melonDS 1.1, https://github.com/melonDS-emu/melonDS/tree/1.1 – GNU GPL v3 or later. Original binaries are redistributed without modification. Exact tagged source is included in `Quelltexte/melonDS-1.1.zip`; its repository contains license notices for Qt, SDL and other dependencies. The displayed melonDS branding is preserved.
- Universal Pokémon Randomizer ZX 4.6.1, https://github.com/Ajarmar/universal-pokemon-randomizer-zx/tree/v4.6.1 – GNU GPL v3 or later. Original JAR with our separately compiled adapter. Exact tagged source and its build files are included in `Quelltexte/Randomizer-ZX-4.6.1.zip`.
- HGSS save format and generation-four encoding/cryptography: informed by PKHeX, https://github.com/kwsch/PKHeX (GNU GPL v3 or later). SoulLink implements a narrowly scoped reader and checkpoint namer.
- Python, https://www.python.org – PSF License. Tcl/Tk – BSD-style licenses. PyInstaller – GPL v2 or later with bootloader exception. These components are included by the application packager.
- Eclipse Temurin OpenJDK 21 in CI builds (or the local JBR OpenJDK 21 runtime), GNU GPL v2 with Classpath Exception. Runtime license files are included under `Runtime/legal`. Upstream source: https://github.com/adoptium/temurin21-binaries and https://github.com/JetBrains/JetBrainsRuntime.

All source code needed to rebuild the SoulLink adapter and launcher is in this repository under `desktop/`. Build instructions are in README.md and `.github/workflows/desktop.yml`. The checkpoint saves contain only initial gameplay state. The user supplies their own game image locally.
