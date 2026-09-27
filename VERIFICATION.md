# Prüfprotokoll

## Updater 0.11 · 27. September 2026

- [Build 36285288308](https://github.com/JohnLegendstyle/SoulLink/actions/runs/36285288308): Windows x64, macOS Apple Silicon und Release-Job erfolgreich; Quellstand `bbb32656ed9174c383ae745ccccb5d1a99a37a94`. Beide Paket-Selbsttests bestanden. Release-Tag verwendet denselben Quellbaum, ohne einen weiteren Überschreibungs-Build auszulösen.

- 56 lokale Python-Tests bestanden, einschließlich Versionsvergleich, Plattformauswahl, Herkunft/Prüfsumme, Archiv-Pfadgrenzen, Symlink-Ausbrüche, unveränderte fremde Dateien und fehlgeschlagene Downloads.
- Versionswechsel bei laufendem Spiel, Cloud-Sitzung/-Abgleich, Rundenbearbeitung und Geräteverbindung gesperrt (gezielte Tests).
- Echte veröffentlichte Windows-x64- und macOS-arm64-Pakete 0.10 über den neuen Updater heruntergeladen, GitHub-SHA256 geprüft und in isolierte temporäre Ordner entpackt. Mac-Symlinks und ausführbare Dateien erhalten. Anschließend Selbsttest der entpackten Mac-App erfolgreich ausgeführt; kein Spiel geöffnet und keine Runde verändert. Windows-EXE lokal nicht ausgeführt.
- Erste Windows-CI-Prüfung scheiterte, weil der simulierte Download vor Installation der Paketabhängigkeiten Zertifikate laden wollte. Der Test isoliert nun den simulierten Transport; alle 56 Tests bestehen auch ohne Site-Packages (zwei vorhandene ndspy-Tests in diesem Modus erwartungsgemäß ausgelassen). Die echte App verwendet unverändert ihren gebündelten Zertifikatsspeicher.
- Gebündelter Zertifikatsspeicher für HTTPS in den eingefrorenen Apps verwendet.
- Nicht durch diese Prüfungen abgedeckt: vollständiger interaktiver Wechsel zwischen zwei gepackten App-Versionen auf den tatsächlichen Rechnern, automatische Wiederherstellung nach einem Absturz der neuen App. Rückfall ist manuelles Starten der alten App.

## Historisch: Prüfung vor dem Spielabend · 26. September 2026

Die folgenden Angaben beschreiben den damaligen Stand, nicht die aktuelle Figuren- oder Tracker-Version.

- Sieben automatische Tests: Start-Saves/Prüfsummen, männliche Trainer Optimus und Bee ohne Pokémon, unveränderte übrige Save-Daten beim Umbenennen, defekte Saves, falsche ROM-Sprache, Pfadgrenzen, Tempo-/Ton-/Tastenprofile und Pokémon-Entschlüsselung.
- Echter lokaler Spieltest: Optimus und Bee werden im WEITER-Menü korrekt angezeigt und starten im Labor. Die Starterauswahl öffnet sich mit drei Pokébällen. Die auszuliefernden Saves enthalten weiterhin keinen Starter.
- In einer getrennten lokalen Testrunde wurde ein Starter angenommen und gespeichert. Art, Name, Trainerkennung, Level und KP werden korrekt gelesen. Der öffentliche Regressionstest verwendet ausschließlich künstliche Daten, keine Rohdaten dieses Testfangs.
- Beide Randomizer-Modi wurden ausgeführt. Jede geschriebene ROM wird erneut geladen und auf drei unterschiedliche Starter mit mindestens einem legendären/mysteriösen Pokémon geprüft. Die Original-ROM wird nur gelesen.
- Der heruntergeladene Mac-Build startet, erstellt über die Oberfläche beide Spielerordner und startet den Emulator aus dem mitgelieferten Paket. Der sichere HTTPS-Aufruf zum Railway-Tracker wurde aus der gebauten App getestet.
- GitHub baut Windows x64 und macOS Apple Silicon jeweils auf dem passenden Betriebssystem. Die Paketprüfung öffnet Tk, prüft beide Saves, startet die Java-Laufzeit und findet den mitgelieferten Emulator und die HTTPS-Zertifikate.
- Der Live-Tracker besteht Prüfungen für Anmeldung/Rundenschlüssel, beide Spieler, Paarbenennung, Speicherung und Übertragung einer K.-o.-Partnersperre.

Nicht geprüft: Spielen auf Eddies tatsächlichem Windows-PC, eine vollständige SoulSilver-Kampagne und jede mögliche zufällige Kombination. Höhere FPS ändern das Spieltempo. Der Tracker liest gespeicherte Zustände, keinen Kampf-Arbeitsspeicher. Siehe SPIELSTART.md.
