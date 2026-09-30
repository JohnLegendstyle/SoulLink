# Versionen und Änderungen

## [0.15.2 – aktuelle stabile Version](https://github.com/JohnLegendstyle/SoulLink/releases/tag/v0.15.2)

30.09.2026 · Windows x64.

Die Abenteuer-Randomisierung verwendet nun die vollständige Schreibstrecke des eingebauten Universal Pokémon Randomizer ZX und prüft die gespeicherte ROM anschließend: wilde Begegnungen und gegnerische Trainerteams müssen sich nachweislich vom Original unterscheiden. Neben den drei Zufallsstartern gibt es einen durchsuchbaren vierten Wunsch-Starter. Die Wahl ersetzt ausschließlich den mittleren Pokéball; links und rechts bleiben zwei verschiedene andere Starter, sodass der Rivale nicht denselben Starter erhält. Korrigierte Speicheradressen im Focus-Emulator reparieren außerdem die Live-Anzeige von Gegnertypen, Schwächen und Attackenwirkung. Bei den neuen Anakin-/Obi-Wan-Figuren sind die beiden seitlichen Laufrichtungen nun korrekt zugeordnet, ohne die freigegebenen Modelle zu verändern. Bestehende Spielstände, Runden, Website-Daten und Tastenprofile bleiben beim Update erhalten; für die reparierte Abenteuer-Randomisierung muss eine neue Runde erstellt werden. [Update-Hinweise](releases/v0.15.2.md).

## [0.15.1](https://github.com/JohnLegendstyle/SoulLink/releases/tag/v0.15.1)

30.09.2026 · Windows x64.

Die kleinen Spielfiguren von Anakin und Obi-Wan wurden vollständig neu aufgebaut. Beide verwenden nun gleichmäßige, schlankere Körperproportionen, klar erkennbare Clone-Wars-Kleidung, Anakins markante Haare beziehungsweise Obi-Wans Haare und Bart sowie korrekt in der Hand sitzende blaue Lichtschwerter. Vorder-, Rück- und Seitenansichten besitzen passende Laufphasen. Spielstände, Runden, Website-Daten und eigene Tasten-/Controllerprofile bleiben unverändert. [Update-Hinweise](releases/v0.15.1.md).

## [0.15.0](https://github.com/JohnLegendstyle/SoulLink/releases/tag/v0.15.0)

30.09.2026 · zunächst Windows x64.

Live-Kampfhilfe im Focus-Emulator mit Gegnertypen, Schwächen und der aktuellen Typenwirkung aller eigenen Attacken. Die drei randomisierten Starter erscheinen pro Spieler im Launcher und können dort vor Spielstart festgelegt werden. Überarbeitete kleine Anakin-/Obi-Wan-Lauffiguren tragen ihre Lichtschwerter in allen Richtungen. Der Windows-Updater ersetzt die App nach Spielende am bisherigen Ort, während Runden, Spielstände und Tastenprofile erhalten bleiben. Der geprüfte Startstand bleibt vor der Starter-Auswahl; Pokéball und Name `T1` werden im Spiel bestätigt. [Update-Schritte und Grenzen](releases/v0.15.0.md).

## [0.14.4](https://github.com/JohnLegendstyle/SoulLink/releases/tag/v0.14.4)

29.09.2026 · Windows x64 und macOS Apple Silicon.

Die Live-Team-Prüfung akzeptiert nun sicher die zusammengehörenden Namen Optimus/Anakin und Bee/Obi-Wan. Ein einzelner vorübergehend unvollständiger Boxplatz verwirft nicht mehr den kompletten geprüften Teamstand; er wird beim nächsten 20-Sekunden-Lauf erneut gelesen. Falls ein anderer Prüfgrund verbleibt, zeigt die App ihn jetzt konkret an. [Update-Schritte](releases/v0.14.4.md).

## [0.14.3](https://github.com/JohnLegendstyle/SoulLink/releases/tag/v0.14.3)

29.09.2026 · Windows x64 und macOS Apple Silicon.

Der Live-Tracker verwendet nun automatisch den mitgelieferten Soul-Link-Emulator. Eine früher ausgewählte normale melonDS-Datei kann den 20-Sekunden-Schnappschuss nicht liefern und wird deshalb beim Update nicht mehr weiterverwendet. Team und Boxen werden auf einem festen 20-Sekunden-Takt übertragen, unabhängig davon, ob sich die `.sav`-Datei geändert hat. Solange noch kein gültiger Live-Stand vorliegt, überschreibt die App die Website nicht mehr still mit dem letzten Speicherstand. Bestehende Spielstände, Runde und Tasten-/Controllerprofile bleiben erhalten. [Update-Schritte](releases/v0.14.3.md).

## [0.14.2](https://github.com/JohnLegendstyle/SoulLink/releases/tag/v0.14.2)

27.09.2026 · Windows x64 und macOS Apple Silicon.

Namensgenaue Soul-Link-Paare: `T11` wird ausschließlich mit `T11` verbunden. Sobald bereits eine höhere T-Nummer erkannt wurde, wird ein fehlender älterer Gegenpart automatisch als gescheiterter Fang ergänzt und der vorhandene Partner gesperrt. Der Live-Team-Abgleich läuft fest alle 20 Sekunden und unabhängig von Cloud-Spielstandversionen. Bestehende Runde, Spielstände und Tastenprofile bleiben erhalten. [Update-Schritte](releases/v0.14.2.md).

## [0.14.1](https://github.com/JohnLegendstyle/SoulLink/releases/tag/v0.14.1)

27.09.2026 · Windows x64 und macOS Apple Silicon.

Live-Lesen aller Boxen ergänzt: Ein neuer Fang wird nun auch bei vollem Team ohne manuelles Speichern erkannt. Für besiegte oder geflüchtete Gegenfänge erscheint beim unvollständigen Paar die Aktion **Besiegt / Fang verpasst**; ein roter Platzhalter hält alle späteren Verbindungen in der richtigen Reihenfolge und sperrt den gefangenen Partner. [Update-Schritte](releases/v0.14.1.md).

## [0.14.0](https://github.com/JohnLegendstyle/SoulLink/releases/tag/v0.14.0)

27.09.2026 · Windows x64 und macOS Apple Silicon.

Live-Kartenmarker für Anakin und Obi-Wan mit ungefähr sekündlichem, kleinem Positionssignal ohne Bild oder Ton. Lokale Ansichten **Karte mittig**, **Fangbuch groß** und **Discord-Platz**. Das aktuelle Team zeigt HGSS-Typen, defensive Schwächen einschließlich ×4 sowie offensive Typvorteile. Bestehende Website-Runde, Spielstände und Tastenprofile bleiben erhalten. [Update-Schritte und Grenzen](releases/v0.14.0.md).

Geprüft: 67 Desktop-Tests, 17 Website-/Protokolltests, Typprüfung, beide Website-Builds und sichtbare Browserprüfung der mittigen Kartenansicht.

## [0.13.0](https://github.com/JohnLegendstyle/SoulLink/releases/tag/v0.13.0)

27.09.2026 · Windows x64 und macOS Apple Silicon.

Bildübertragung entfernt: kein Capture-/Upload-Start in der App, auch nicht durch alte Einstellungen oder geerbte Umgebungsvariablen. Alte Website-Bild-Endpunkte sind abgeschaltet. Teams, Fangdaten und Cloud-Saves bleiben aktiv. Website mit kompakter Teamübersicht, Fangkarte, Soul-Link-Paaren und optionalem größenverstellbarem Discord-Platzhalter (bei Eddie standardmäßig an). Kein eingebetteter Discord-Stream.

In alten laufenden Apps „Übertragung stoppen“, anschließend in einer Spielpause aktualisieren. Tastenprofile aus 0.12.1 bleiben erhalten. [Update-Schritte und Grenzen](releases/v0.13.0.md). 65 Python-Tests, 15 Website-/Protokolltests, Typprüfung und Website-Build; neue Website mit realen Teamständen visuell geprüft. Alte Übertragungsprotokoll-Tests bleiben als historische Regressionstests vorhanden, werden aber nicht mehr von der Website verwendet.

## [0.12.1](https://github.com/JohnLegendstyle/SoulLink/releases/tag/v0.12.1)

27.09.2026 · Windows x64 und macOS Apple Silicon.

Versionsunabhängige vollständige Tasten-/Controllerprofile pro lokalem Spieler, Übernahme alter Profile, Sicherung der Vorgängerversion, Erhalt deaktivierter/modifizierter/rechter Tasten und zusätzlicher Hotkeys. Tastenübernahme unabhängig von Grafik-Einstellungen; atomare Speicherung der Launcher-Einstellungen. Bewusste Änderungen im Launcher haben Vorrang vor alten Profilen und werden auch vor dem Update-Wechsel gespeichert. Enthält den FPS-Fix aus 0.12.0. [Update-Schritte und Wiederherstellungsgrenzen](releases/v0.12.1.md).

64 Python-Tests inklusive simuliertem Emulator-Versionswechsel, Profil-Isolation, defekter Grafik-Konfiguration, Sicherungswiederherstellung und Tastenänderungen im Launcher. Tatsächliche lokale Einstellungen auf den Rechnern der Spieler sind nicht von hier überprüft.

## [0.12.0](https://github.com/JohnLegendstyle/SoulLink/releases/tag/v0.12.0)

27.09.2026 · Windows x64 und macOS Apple Silicon.

Direkte lokale Bildleitung statt Dateipolling, weniger Sendepausen und größere begrenzte Pakete. Die Website taktet anhand tatsächlich empfangener Bilder statt der eingestellten Ziel-FPS. Übertragungsvorschau maximal 720 × 540; interne Spielauflösung unverändert. Beide Apps aktualisieren, Website neu laden. [Update-Schritte und Grenzen](releases/v0.12.0.md).

Geprüft: 58 lokale Python-Tests, 15 Website-/Protokolltests, Typprüfung und Website-Build. Der Lasttest überträgt 240 synthetische 16-KB-Bildpakete mit 120 FPS trotz 300-ms-Empfangsbestätigungen vollständig. Das ist keine Messung auf euren Windows-Rechnern.

## Website · 27.09.2026 (kein App-Update erforderlich)

- Volle Fensterbreite; Anakins Team links neben seinem Spielbild, Obi-Wans Team rechts.
- Fehlende Fangorte bekannter Pokémon werden aus bereits gespeicherten Cloud-Spielständen nachgetragen (Pokémon-Bericht/Herkunftsort). Teams, K.-o.-Status, manuelle Markierungen und Save-Dateien bleiben unverändert. Nicht mehr vorhandene Pokémon lassen sich nur zuordnen, wenn sie noch in einem aufbewahrten Cloud-Spielstand enthalten sind.

## [0.11.0](https://github.com/JohnLegendstyle/SoulLink/releases/tag/v0.11.0)

27.09.2026 · Windows x64 und macOS Apple Silicon.

Eingebauter Updater: automatische Versionsprüfung, Änderungsübersicht, bestätigter Download mit SHA256-Prüfung und separate Installation. Wechsel ist bei laufendem Spiel oder Cloud-Abgleich gesperrt. Alte App und Spielstände bleiben erhalten. [Update-Schritte und Grenzen](releases/v0.11.0.md). 0.11 muss einmalig manuell heruntergeladen werden.

## [0.10.0](https://github.com/JohnLegendstyle/SoulLink/releases/tag/v0.10.0)

27.09.2026 · Windows x64 und macOS Apple Silicon.

Überarbeitete 45 Jedi-Designs, Fangort-Übertragung und Fangkarte, aktuelle Teams neben den Spielbildern. [Downloads, sichere Update-Schritte und Einschränkungen](releases/v0.10.0.md).

Die Website wird unabhängig von der Desktop-App veröffentlicht. Der Pixel-Regionskartenlook ist ein Website-Update; keine Desktop-Version 0.10.1.

## Frühere Zwischenstände 0.5 bis 0.9

Diese Stände wurden über den fortlaufend ersetzten Download `spielabend` verteilt. Es gibt dafür aktuell keine getrennt archivierten Versionspakete. Sie werden daher nicht als reproduzierbare alte Downloads angeboten.

- 0.9: Live-Team-Abgleich etwa alle 25 Sekunden und Übertragungsverbesserungen.
- 0.8: Clone-Wars-Figuren und Spielernamen Anakin/Obi-Wan.
- 0.7: Bildübertragung mit FPS-Metadaten der App, ohne Ton.
- 0.6: Cloud-Spielstandabgleich zwischen Windows und Mac.
- 0.5: Geschützte Website und Geräteverbindung.

## Archivierte Downloads

Diese älteren Pakete bleiben unverändert erhalten. Sie sind nicht für den aktuellen gemeinsamen Spielbetrieb empfohlen und besitzen nicht den Funktionsumfang von 0.10.0.

- [0.4.0](https://github.com/JohnLegendstyle/SoulLink/releases/tag/v0.4.0)
- [0.3.0](https://github.com/JohnLegendstyle/SoulLink/releases/tag/v0.3.0)
- [0.2.0](https://github.com/JohnLegendstyle/SoulLink/releases/tag/v0.2.0)

## Was bedeutet „spielabend“?

`spielabend` ist der technische, fortlaufend ersetzte Build-Kanal. Er ist **kein Versionsarchiv**. Für eine nachvollziehbare Installation immer einen nummerierten Release wie `v0.10.0` verwenden.
