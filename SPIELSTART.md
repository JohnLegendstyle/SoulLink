# Soul Link · Optimus und Bee

1. Passende ZIP für Windows oder macOS herunterladen und **vollständig entpacken**. SoulLink und die Ordner Emulator und Runtime zusammenlassen.
2. `SoulLink.exe` (Windows) oder `SoulLink.app` (Mac) starten. Die neue App ist noch nicht mit einem kommerziellen Zertifikat signiert. Falls das Betriebssystem beim ersten Start nachfragt, nur das selbst heruntergeladene SoulLink-Paket freigeben.
3. Eure eigene deutsche **Pokémon SoulSilver-ROM (.nds, Spielcode IPGD)** auswählen. Emulator und Java sind im Download enthalten.
4. **Neue randomisierte Runde erstellen**. Beide Spieler erhalten eigene ROMs und Spielstände in einem neuen Ordner. Die Original-ROM wird nicht verändert.
5. **Optimus starten** oder **Bee starten**. Im Spiel **WEITER** wählen: Ihr steht als männlicher Trainer direkt vor der Starter-Auswahl. Die drei Pokémon wählt ihr selbst. Mindestens eines pro Auswahl ist legendär (einschließlich mysteriöser Pokémon).

Standardmäßig werden auch wilde Pokémon und gegnerische Trainerteams zufällig geändert. Die Option kann abgewählt werden: Dann ändern sich nur die Starter und die dazugehörigen Rivalen-Starter. Level, Attacken, Typen und Werte behalten ihre normale Logik; geskriptete Geschenke/statische Begegnungen bleiben unverändert.

## Gemeinsam oder getrennt erstellen

Jede Erstellung erzeugt zwei getrennte Spielerordner. Ihr könnt unabhängig auf euren Rechnern eine Runde erstellen und jeweils euren Spieler starten. Für exakt dieselbe Runde lässt sich der eigene Runden-Ordner zwischen euren Rechnern übertragen. Auf GitHub liegen keine ROM-Dateien. Vorhandene Runden über **Vorhandene Runde öffnen → runde.json** laden. Nach einem App-Neustart wird die letzte Runde wieder angeboten.

## Bedienung

Standardtasten: **X = A/Bestätigen**, **Z = B/Zurück**, **S = DS-X/Menü**, **A = DS-Y**, **Pfeile = Bewegen**, **Return = Start**, **Shift = Select**, **Q/W = L/R**, **Tab = Schnelllauf**, **F11 = Vollbild umschalten**. Unter Grafik · Sound · Tasten lassen sich diese Tasten ändern. Im Spiel kann der untere Bildschirm mit der Maus bedient werden.

60 FPS ist normales Spieltempo. 90/120 FPS und unbegrenzt beschleunigen auch Spiel und Ton; das fügt dem Originalspiel keine neuen Animationsbilder hinzu. Die interne Auflösung macht 3D-Flächen schärfer, nicht die ursprünglichen 2D-Sprites. Bei Leistungseinbrüchen 2× oder 1× wählen. Einstellungen gelten ab dem nächsten Spielstart.

**Speichert regelmäßig über SPEICHERN im Spiel.** Speichert vor dem Schließen des Spielfensters. Für einen Gerätewechsel den ganzen Runden-Ordner einschließlich `.sav` kopieren. Die mitgelieferten Checkpoints dienen nur neuen Runden und werden nie über einen bestehenden Fortschritt kopiert.

## Gemeinsamer Tracker

https://soullink-web-production.up.railway.app

Eine gemeinsame Tracker-Runde erstellen, je eine Verbindungsdatei für Optimus und Bee herunterladen und die passende Datei im Reiter Gemeinsamer Tracker wählen. Den eigenen `.sav` auswählen und die Synchronisierung starten. Verbindungsdateien enthalten persönliche Rundenschlüssel und gehören nicht auf GitHub.

Der Tracker liest **gespeicherte Spielstände**, keine flüchtigen Kampfdaten. Änderungen erscheinen nach dem Speichern. Ein K. o. wird nur erkannt, wenn mit 0 KP gespeichert wurde. Paare entstehen nach der Reihenfolge erstmals gespeicherter Fänge. Gesperrte Partner werden im Tracker und in der App angezeigt; ihr müsst eure Soul-Link-Regel selbst im Spiel einhalten.

## Plattformen

Windows-Paket: 64-Bit Intel/AMD. Mac-Paket: Apple Silicon (M1 oder neuer). Ein Windows-Build ersetzt keinen Test auf eurem tatsächlichen PC. Der melonDS-Spielkern öffnet ein eigenes Fenster; der moderne Launcher übernimmt Runden, Einstellungen und Tracker.
