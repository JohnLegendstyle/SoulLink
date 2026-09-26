# Third-party software

- Certifi 2026.7.22, https://github.com/certifi/python-certifi – MPL 2.0. Unmodified Mozilla root certificates are bundled for verified HTTPS connections on both platforms.
- ndspy 4.2.0, https://github.com/RoadrunnerWMC/ndspy – GNU GPL v3 or later. Used to validate Nintendo DS filesystem and texture containers. Unmodified source is included as `Quelltexte/ndspy-4.2.0.tar.gz`.

SoulLink desktop code and its Java adapter are provided under GNU GPL v3 or later; see LICENSE. No Nintendo ROM, BIOS, firmware dump or copyrighted game media is included in releases.

The replacement robot sprite sheets are AI-generated fan art, not extracted game graphics. Optimus Prime, Bumblebee and Transformers are characters/marks of their respective rights holders; this project is unofficial and not endorsed. Artwork provenance and generation prompts: `desktop/assets/skins/README.md`.

- melonDS 1.1, https://github.com/melonDS-emu/melonDS/tree/1.1 – GNU GPL v3 or later. Version 0.4 adds the SoulLink Focus Qt frontend and screen-layout changes, without changing the emulation core. Original source: `Quelltexte/melonDS-1.1.zip`; complete modified source: `Quelltexte/SoulLink-Focus-source.zip`. Source patch and build instructions: `desktop/focus/`. Original About dialog and advanced menus remain under Mehr. This is an unofficial derivative, not an official melonDS release.
- Focus dynamically links Qt 6, SDL2, libarchive, enet, zstd and faad2. Upstream source and licenses: https://code.qt.io (Qt LGPL/GPL), https://github.com/libsdl-org/SDL (zlib), https://github.com/libarchive/libarchive (BSD), https://github.com/lsalzman/enet (MIT), https://github.com/facebook/zstd (BSD/GPL), https://github.com/knik0/faad2 (GPL). Rebuild and replaceable-library instructions are in `desktop/focus/README.md`.
- Universal Pokémon Randomizer ZX 4.6.1, https://github.com/Ajarmar/universal-pokemon-randomizer-zx/tree/v4.6.1 – GNU GPL v3 or later. Original JAR with our separately compiled adapter. Exact tagged source and its build files are included in `Quelltexte/Randomizer-ZX-4.6.1.zip`.
- HGSS save format and generation-four encoding/cryptography: informed by PKHeX, https://github.com/kwsch/PKHeX (GNU GPL v3 or later). SoulLink implements a narrowly scoped reader and checkpoint namer.
- Python, https://www.python.org – PSF License. Tcl/Tk – BSD-style licenses. PyInstaller – GPL v2 or later with bootloader exception. These components are included by the application packager.
- Eclipse Temurin OpenJDK 21 in CI builds (or the local JBR OpenJDK 21 runtime), GNU GPL v2 with Classpath Exception. Runtime license files are included under `Runtime/legal`. Upstream source: https://github.com/adoptium/temurin21-binaries and https://github.com/JetBrains/JetBrainsRuntime.

All source code needed to rebuild the SoulLink adapter and launcher is in this repository under `desktop/`. Build instructions are in README.md and `.github/workflows/desktop.yml`. The checkpoint saves contain only initial gameplay state. The user supplies their own game image locally.
