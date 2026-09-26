# SoulLink Focus frontend

Design 3: matte graphite/amber interface, large primary DS display with a smaller top-aligned touchscreen, compact lower control bar and settings popovers. The rendered game and touchscreen are real melonDS output, not streamed screenshots or a mock-up. Both preserve 4:3 proportions. The Tk launcher remains responsible for ROM randomization, save-safe round management and tracker synchronization; it hides while Focus is running and returns afterward.

`FocusWindow.inc` adds Qt widgets to the pinned melonDS 1.1 frontend. `apply_focus.py` performs exact-source-checked transformations. The emulation core and save implementation are not modified. `test_layout.cpp` verifies display boundaries, aspect ratio and reverse touch coordinates without a game ROM. The complete modified source is distributed alongside every package.

Controls: pause/resume, live volume, existing native key binding dialog, live 1–16× 3D resolution, nearest/linear pixel filtering, integer scaling, three screen layouts, 60/90/120/unlimited FPS, fullscreen. Higher FPS changes game speed. Pixel filtering does not increase sprite detail. Original menus and About remain under Mehr. New round/player switching requires confirmation to close the current game; it never claims to save automatically.

The launcher supplies a unique local request path to the child process. On close, requests are restricted to `new-round`, `start:Optimus` and `start:Bee`. No network listener or shell execution is used. Settings changed inside Focus are imported after process exit. Each binary build gets an isolated emulator folder so an old copy cannot silently shadow an upgrade.

## Build

CI uses the existing desktop workflow. `prepare_runtime.py` downloads the pinned upstream source, then invokes `build_focus.py`. macOS dependencies: Homebrew qtbase, qtmultimedia, qtsvg, sdl2, libarchive, enet, zstd, faad2, pkg-config, cmake, ninja. Windows dependencies: MSYS2 UCRT64 GCC/CMake/Ninja, corresponding libraries and Qt6 packages. Only disposable CI runners automatically install dependencies; a local build requires them already installed. The fallback MSYS2 base archive is pinned and SHA-256 verified. Building requires network access to official upstream/package repositories.

Fresh build command: `python prepare_runtime.py`, then the packaging instructions in the root README. Focus output is `desktop/vendor/FocusEmulator`. Delete or move only generated build directories before a rebuild; keep saved rounds separate. The original engine source and the Focus-modified source with its CMake build file are in release `Quelltexte/`. DLLs/frameworks are dynamically linked and can be replaced with ABI-compatible builds; macOS may require renewed ad-hoc signing after modifying a bundle. Source for dynamically linked dependencies is available through the upstream projects listed in THIRD_PARTY_NOTICES.md and their corresponding package-manager source recipes.

This is not a full character-art overhaul. Version 0.3's robot walking/running skins remain unchanged; other portraits and special animations retain the original art.
