# Soul Link · Optimus × Bee

Desktop-Launcher für deutsche Pokémon SoulSilver-ROMs mit lokalem Randomizer, überprüfbaren Start-Spielständen und gemeinsamem Railway-Tracker.

- [Downloads](https://github.com/JohnLegendstyle/SoulLink/releases)
- [Spielstart und Bedienung](SPIELSTART.md)
- [Gemeinsamer Tracker](https://soullink-web-production.up.railway.app)

Der Nutzer liefert seine eigene ROM. Dieses Repository und die Releases enthalten keine Nintendo-ROMs oder BIOS-Dumps.

## Desktop

`desktop/` enthält den dunklen Launcher für Windows/macOS, den Randomizer-Adapter und den HGSS-Save-Reader. Drei eindeutige Starter, mindestens ein legendäres/mysteriöses Pokémon; optional wilde Begegnungen und Trainerteams. Getrennte männliche Trainer Optimus und Bee starten direkt vor der Auswahl. Jede Runde hat ein neues Verzeichnis. Die letzte Runde kann wieder geöffnet werden. melonDS bleibt der Spielkern und öffnet ein separates Fenster.

Python 3.12 mit Tk, Java 21 und ein JDK mit javac/jlink werden zum Bauen benötigt:

```sh
cd desktop
python prepare_runtime.py
python -m unittest discover -s tests -v
python -m pip install -r requirements-build.txt
pyinstaller --clean --noconfirm SoulLink.spec
python package_release.py
```

Die GitHub Action baut Windows x64 und macOS Apple Silicon auf eigenen Systemen und veröffentlicht ZIP-Pakete. Emulator, Java-Laufzeit, Lizenzen und getaggte Drittanbieter-Quelltexte liegen in jedem Paket. Der lokale Build ist nicht mit einem kommerziellen Signaturzertifikat signiert.

## Tracker

Version 0.6 adds private full `.sav` synchronization between macOS and Windows. `railway/cloud.mjs` stores the last ten immutable versions per room/player on the persistent SQLite volume. ROM hashes prevent mixing randomized games; compare-and-swap revisions and a renewable 90-second session lease prevent concurrent writers. The desktop validates checksums, compares its last shared baseline, prompts on divergence, and saves a local backup before an atomic download replacement. Downloads only happen before launching the emulator; uploads happen after in-game saves and on game exit. No ROM data is uploaded. One-time setup and limitations are in SPIELSTART.md. Both computers must run 0.6+ and have the identical local round.

Cloud tests: `PYTHONPATH=desktop python -m unittest discover -s desktop/tests -v` and `SOULLINK_TEST_PYTHON=/absolute/path/to/python node --test railway/tests/*.test.mjs`. The optional Python integration simulates Mac → Windows → Mac using separate temporary directories and an isolated server, including real uploads, downloads, conflicts, retained copies and session locks. Never run these tests against production.

Version 0.5 adds password-protected website accounts (John/Eddie), one-time browser-confirmed device pairing, automatic saved-team sync and private DS-only previews (up to 4 fps, no audio). The server requires `SOULLINK_PASSWORD_HASH` as `salt:scrypt(password,salt,32).hex`; never commit passwords or grants. HTTPS cookies are HttpOnly and SameSite=Lax. `SOULLINK_LOCAL_TEST=1` is only for loopback integration tests. Account room keys are encrypted in SQLite; existing rooms remain intact. Preview frames are bounded, memory-only and expire after six seconds. Tests: `node --test railway/tests/online.test.mjs`.

`railway/server.mjs`: Node 24 mit SQLite, Bearer-Rundenschlüsseln und persistentem Volume unter `/data`. Die statische React-Seite wird mit `node node_modules/vite/bin/vite.js build --config railway/vite.config.ts` gebaut. `DATA_DIR=/data`, `PUBLIC_DIR=/app/public` und `PORT` konfigurieren den Server. Bestehende interne Rollen John/Eddie bleiben aus Kompatibilitätsgründen erhalten; die sichtbaren Namen sind Optimus/Bee.

Die Desktop-App liest gespeicherte `.sav`-Dateien, keinen laufenden Arbeitsspeicher. K. o.-Erkennung und Paarbildung sind dadurch auf gespeicherte Zustände beschränkt. Regeln und Grenzen stehen in SPIELSTART.md. Verbindungsdateien enthalten private Schlüssel und werden niemals in Releases veröffentlicht.

## Lizenz

SoulLink-Desktopcode und Adapter: GPL-3.0-or-later. Drittanbieterhinweise und zugehörige Quelltexte: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
