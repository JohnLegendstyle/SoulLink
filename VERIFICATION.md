# Prüfung vor dem Spielabend · 26. September 2026

- Sieben automatische Tests: Start-Saves/Prüfsummen, männliche Trainer Optimus und Bee ohne Pokémon, unveränderte übrige Save-Daten beim Umbenennen, defekte Saves, falsche ROM-Sprache, Pfadgrenzen, Tempo-/Ton-/Tastenprofile und Pokémon-Entschlüsselung.
- Echter lokaler Spieltest: Optimus und Bee werden im WEITER-Menü korrekt angezeigt und starten im Labor. Die Starterauswahl öffnet sich mit drei Pokébällen. Die auszuliefernden Saves enthalten weiterhin keinen Starter.
- In einer getrennten lokalen Testrunde wurde ein Starter angenommen und gespeichert. Art, Name, Trainerkennung, Level und KP werden korrekt gelesen. Der öffentliche Regressionstest verwendet ausschließlich künstliche Daten, keine Rohdaten dieses Testfangs.
- Beide Randomizer-Modi wurden ausgeführt. Jede geschriebene ROM wird erneut geladen und auf drei unterschiedliche Starter mit mindestens einem legendären/mysteriösen Pokémon geprüft. Die Original-ROM wird nur gelesen.
- Der heruntergeladene Mac-Build startet, erstellt über die Oberfläche beide Spielerordner und startet den Emulator aus dem mitgelieferten Paket. Der sichere HTTPS-Aufruf zum Railway-Tracker wurde aus der gebauten App getestet.
- GitHub baut Windows x64 und macOS Apple Silicon jeweils auf dem passenden Betriebssystem. Die Paketprüfung öffnet Tk, prüft beide Saves, startet die Java-Laufzeit und findet den mitgelieferten Emulator und die HTTPS-Zertifikate.
- Der Live-Tracker besteht Prüfungen für Anmeldung/Rundenschlüssel, beide Spieler, Paarbenennung, Speicherung und Übertragung einer K.-o.-Partnersperre.

Nicht geprüft: Spielen auf Eddies tatsächlichem Windows-PC, eine vollständige SoulSilver-Kampagne und jede mögliche zufällige Kombination. Höhere FPS ändern das Spieltempo. Der Tracker liest gespeicherte Zustände, keinen Kampf-Arbeitsspeicher. Siehe SPIELSTART.md.
