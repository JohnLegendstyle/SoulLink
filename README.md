# Soul Link · Anakin × Obi-Wan

Desktop-Launcher für deutsche Pokémon SoulSilver-ROMs mit lokalem Randomizer, überprüfbaren Start-Spielständen und gemeinsamem Railway-Tracker.

- **[Aktuelle stabile Version: 0.10.0](https://github.com/JohnLegendstyle/SoulLink/releases/tag/v0.10.0)**
- [Windows 64 Bit herunterladen](https://github.com/JohnLegendstyle/SoulLink/releases/download/v0.10.0/SoulLink-0.10.0-Windows-x64.zip)
- [macOS Apple Silicon herunterladen](https://github.com/JohnLegendstyle/SoulLink/releases/download/v0.10.0/SoulLink-0.10.0-macOS-arm64.zip)
- [Versionsübersicht und Änderungsverlauf](CHANGELOG.md)
- [Update 0.10.0: Spielstände behalten und neue Jedi-Grafiken aktivieren](releases/v0.10.0.md)
- [Spielstart und Bedienung](SPIELSTART.md)
- [Gemeinsamer Tracker](https://soullink-web-production.up.railway.app)

Der Nutzer liefert seine eigene ROM. Dieses Repository und die Releases enthalten keine Nintendo-ROMs oder BIOS-Dumps. **Beim Update die bestehende Runde öffnen; keine Startspielstände über euren Fortschritt kopieren.** Der Downloadkanal `spielabend` wird fortlaufend ersetzt; nummerierte Releases sind die verlässliche Versionsablage. macOS-Pakete sind für M1 oder neuer, nicht für Intel-Macs.

## Desktop

`desktop/` enthält den dunklen Launcher für Windows/macOS, den Randomizer-Adapter und den HGSS-Save-Reader. Drei eindeutige Starter, mindestens ein legendäres/mysteriöses Pokémon; optional wilde Begegnungen und Trainerteams. Getrennte männliche Trainer Anakin (John) und Obi-Wan (Eddie) starten direkt vor der Auswahl. Jede Runde hat ein neues Verzeichnis. Die letzte Runde kann wieder geöffnet werden. melonDS bleibt der Spielkern und öffnet ein separates Fenster. Version 0.8 enthält ein lokal handgezeichnetes Clone-Wars-Grafikpaket, ohne Bildgenerator/API; Umfang und Grenzen siehe `desktop/assets/jedi/README.md`.

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

Version 0.7 replaces low-rate screenshot polling with an authenticated HTTP frame stream. The GL panel captures each rendered frame, GPU-downscales before readback, and encodes JPEGs on a bounded latest-only worker. FPS metadata follows native settings without a fixed capture throttle. Python maintains a chunked TLS upload; Node relays bounded packets with backpressure handling to authenticated browser fetch streams. The canvas reports source target, received FPS and displayed FPS separately. No audio or desktop capture; no promise that hardware/network/display limits can be exceeded. Streams reconnect periodically and hidden tabs disconnect. Local protocol tests include 120 FPS and fragmented/coalesced packets.

Version 0.6 adds private full `.sav` synchronization between macOS and Windows. `railway/cloud.mjs` stores the last ten immutable versions per room/player on the persistent SQLite volume. ROM hashes prevent mixing randomized games; compare-and-swap revisions and a renewable 90-second session lease prevent concurrent writers. The desktop validates checksums, compares its last shared baseline, prompts on divergence, and saves a local backup before an atomic download replacement. Downloads only happen before launching the emulator; uploads happen after in-game saves and on game exit. No ROM data is uploaded. One-time setup and limitations are in SPIELSTART.md. Both computers must run 0.6+ and have the identical local round.

Cloud tests: `PYTHONPATH=desktop python -m unittest discover -s desktop/tests -v` and `SOULLINK_TEST_PYTHON=/absolute/path/to/python node --test railway/tests/*.test.mjs`. The optional Python integration simulates Mac → Windows → Mac using separate temporary directories and an isolated server, including real uploads, downloads, conflicts, retained copies and session locks. Never run these tests against production.

Version 0.5 adds password-protected website accounts (John/Eddie), one-time browser-confirmed device pairing, automatic saved-team sync and private DS-only previews (up to 4 fps, no audio). The server requires `SOULLINK_PASSWORD_HASH` as `salt:scrypt(password,salt,32).hex`; never commit passwords or grants. HTTPS cookies are HttpOnly and SameSite=Lax. `SOULLINK_LOCAL_TEST=1` is only for loopback integration tests. Account room keys are encrypted in SQLite; existing rooms remain intact. Preview frames are bounded, memory-only and expire after six seconds. Tests: `node --test railway/tests/online.test.mjs`.

`railway/server.mjs`: Node 24 mit SQLite, Bearer-Rundenschlüsseln und persistentem Volume unter `/data`. Die statische React-Seite wird mit `node node_modules/vite/bin/vite.js build --config railway/vite.config.ts` gebaut. `DATA_DIR=/data`, `PUBLIC_DIR=/app/public` und `PORT` konfigurieren den Server. Bestehende interne Rollen John/Eddie und lokale Rundenkennungen Optimus/Bee bleiben aus Kompatibilitätsgründen erhalten; die sichtbaren Namen sind Anakin/Obi-Wan.

Ab 0.9 liest die Desktop-App zusätzlich das aktuelle Team aus dem Emulator etwa alle 25 Sekunden. Boxen und vollständiger Spielstand werden weiterhin aus `.sav` gelesen; der Cloud-Spielstandabgleich benötigt Speichern im Spiel. Ab 0.10 werden außerdem Fangorte übertragen. Regeln und Grenzen stehen in SPIELSTART.md. Verbindungsdateien enthalten private Schlüssel und werden niemals in Releases veröffentlicht.

## Lizenz

SoulLink-Desktopcode und Adapter: GPL-3.0-or-later. Drittanbieterhinweise und zugehörige Quelltexte: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
