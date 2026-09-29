# Soul Link · Anakin und Obi-Wan

## Update 0.15: Windows-Kampfhilfe, Starterwahl und Direkt-Update

Diese Version wird zunächst nur als **Windows-x64-Paket** ausgeliefert. Im Focus-Spielfenster erscheint im Kampf rechts unten eine Live-Hilfe: Typen und Schwächen des gegnerischen Pokémon sowie die vier Attacken des eigenen aktiven Pokémon mit **keine Wirkung**, **nicht effektiv**, **effektiv** oder **sehr effektiv**. Die Daten werden ausschließlich aus dem laufenden Spiel gelesen; es wird weder gespeichert noch der Kampf verändert.

Bei einer neuen Runde zeigt der Launcher für Anakin und Obi-Wan jeweils die drei erzeugten Starter. Erst einen Starter markieren und **Auswählen · im Spiel T1 nennen** drücken, danach das Spiel starten. Mindestens einer der drei Vorschläge ist legendär oder mysteriös. Der geprüfte Spielstand bleibt aus Sicherheitsgründen direkt vor der Auswahl: im Labor nur noch den Pokéball bestätigen und den Starter **T1** nennen. Ein ungetesteter Sprung über Story-Ereignisse bis zum Fangtutorial wird nicht vorgenommen.

Das Windows-Update ersetzt nach Bestätigung die Programmdateien im bisherigen Soul-Link-Ordner und startet die App neu. Spielstände, Runden, Website-Verbindung und Tastenprofile liegen außerhalb beziehungsweise bleiben als eigene Dateien unberührt. Ersetzte Programmteile werden vorher in einer Rückfallkopie gesichert. Vor dem Update im Spiel speichern, beide Spielfenster schließen und den Cloud-Abgleich abwarten.

Anakin und Obi-Wan besitzen überarbeitete kleine Laufansichten mit klarerem Körperbau, eigener Gesichts-/Haarform und blauem Lichtschwert in Vorder-, Seiten- und Rückenansicht. Bei einer bestehenden Runde nach dem Update einmal **Figuren aktualisieren** ausführen; der Spielstand wird dabei nicht ersetzt.

## Update 0.14: Live-Karte, Typenhilfe und Discord-Ansicht

Die eingebaute Bildübertragung wurde entfernt. Für den echten, speicherunabhängigen 20-Sekunden-Teamabgleich aktualisieren beide in einer Spielpause auf **0.14.4**. Spielstände, Website-Runde und eigene Tastenprofile bleiben erhalten. Die Website lehnt alte Bild-Uploads ab. Teams, Fangkarte und Cloud-Spielstände bleiben aktiv. Oben wählt jeder Browser seine eigene Ansicht: **Karte mittig**, **Fangbuch groß** oder **Discord-Platz**. Kein eingebetteter Stream.

## Update 0.12.1: eigene Tasten behalten

Tastatur, Controller und zusätzliche Hotkeys liegen jetzt versionsunabhängig im Benutzerprofil unter `SoulLink/Controls`, getrennt nach lokalem Spieler. Die neueste gültige Belegung aus alten Emulator-Profilen wird übernommen; alte Profilordner bitte bis zur Kontrolle behalten. Deaktivierte Tasten und Sondertasten bleiben erhalten. Bereits überschriebene Einstellungen können nur aus noch vorhandenen alten Profilen zurückgeholt werden. Keine neue Runde nötig. Direkt von 0.11 auf 0.12.1 aktualisieren; 0.12.0 ist kein notwendiger Zwischenschritt.

## Update 0.12: Bildübertragung

Beide Spieler aktualisieren die App im Reiter **Updates** (oder die aktuelle ZIP separat entpacken) und laden die Website neu. Die neue lokale Bildleitung vermeidet verlorene Bilder durch überschriebene Dateien. Empfangene Bilder werden auf der Website gleichmäßiger abgespielt. Nur die Übertragungsvorschau ist auf maximal 720 × 540 begrenzt; eure interne Spielauflösung bleibt erhalten. Vor dem App-Wechsel im Spiel speichern, Spiel schließen und Cloud-Abgleich abwarten. Bestehende Runde öffnen, keine Startspielstände importieren. FPS bleiben von Verbindung, Rechner und Bildschirm abhängig.

## Update 0.11: App-Updater

0.11 einmalig manuell herunterladen. Danach prüft der Reiter **Updates** beim Start auf stabile GitHub-Versionen, zeigt Änderungen und bietet einen bestätigten Download mit Prüfsummenprüfung an. Die neue App liegt separat im Benutzerprofil unter `SoulLink/Updates`; alte App, Runde, Einstellungen und Website-Verbindung bleiben erhalten.

Zum Wechsel **im Spiel speichern**, Spielfenster schließen und Cloud-Abgleich abwarten, dann **Zur neuen Version wechseln**. Kein Wechsel während eines laufenden Spiels oder Abgleichs. Bestehende Runde weiterverwenden; keine Startspielstände importieren. Verknüpfungen werden nicht umgebogen: Die neue App am im Updater angezeigten Pfad starten bzw. neu anheften. Grafikänderungen bleiben eine getrennte Aktion im Spiel-Menü. Alte Apps werden nicht automatisch gelöscht.

## Update 0.10: neuer Pixelstil, Fangkarte und Teams am Spielbild

- Alle 45 vorhandenen Jedi-Designs sind im freigegebenen Pixelstil überarbeitet, einschließlich Anakin und Obi-Wan. Plo Koons und Yodas bestätigte Vorderansichten bleiben erhalten. Lauf-/Rennfiguren sowie vordere und hintere Trainer-Kampfbilder sind enthalten; die bisherigen Grenzen bei Fahrrad, Surfen, Angeln und Trainerpass bleiben bestehen.
- Die Website zeigt für beide Spieler die sechs aktuellen Teamplätze, Level, KP, Typen, Schwächen und Partnersperren. Die Teamdaten kommen ab App 0.14.3 aus dem integrierten Live-Emulator fest alle 20 Sekunden; ein noch nicht vorliegender oder veralteter Live-Stand wird entsprechend beschriftet.
- Ab App 0.14.0 erscheinen Anakin und Obi-Wan als Marker auf der Fangkarte. Nur Karten-ID, Koordinaten, Blickrichtung und Zeitpunkt werden ungefähr jede Sekunde übertragen; kein Bild und kein Ton. Mit dem jeweiligen Spielerknopf springt die Karte zu seiner Region und Route.
- Die Johto-/Kanto-Karte zeigt pro Ort links Anakin, rechts Obi-Wan. Ab App 0.14.3 werden Herkunftsorte aus dem laufenden Team **und aus allen Boxen** alle 20 Sekunden gelesen; ein Fang bei vollem Team erscheint daher auch ohne manuelles Speichern. Bereits erfasste Pokémon bleiben im Fangbuch, auch wenn sie später aus dem Team verschwinden.
- Grün bedeutet Fang/Erhalt erkannt (auch Starter und Geschenke können dazugehören), grau bedeutet **kein Fang erfasst**, nicht automatisch noch frei. Eier und Pokémon aus anderen Editionen werden nicht als HGSS-Fang gewertet. Wurde der Gegenfang besiegt oder ist geflüchtet, klickt der betroffene Spieler beim unvollständigen Paar auf **Besiegt / Fang verpasst**. Die Website setzt einen roten Platzhalter, sperrt den gefangenen Partner und hält alle späteren Paare in der richtigen Reihenfolge. Nur der eigene angemeldete Spieler kann seine Markierungen ändern.

**Bestehende Runde behalten:** Im Spiel speichern, Spielfenster schließen und Cloud-Abgleich abwarten. Neues ZIP in einen separaten Ordner entpacken, neue SoulLink-App öffnen und im Menü **Spiel → Clone Wars: Anakin & Obi-Wan anwenden** die neuen Grafiken auf eure bestehende Runde anwenden. Keine neue Zufallsrunde erstellen und keine Startspielstände über eure Saves kopieren. Vorhandene Sicherungen und die Cloud-Zuordnung bleiben erhalten.

## Update 0.9: einfachere Übertragung und Live-Teams

**Während einer laufenden Runde nichts ersetzen.** Erst in eurer Spielpause im Spiel speichern, Cloud-Abgleich abwarten und die App schließen. Dann das neue ZIP vollständig in einen neuen Ordner entpacken und daraus starten. Runden und Einstellungen bleiben außerhalb des App-Ordners erhalten. Den vorhandenen Rundenordner weiterverwenden, keine neue Zufallsrunde erzeugen.

Die untere Verbindungsleiste zeigt **Übertragung starten/stoppen**, **Neu verbinden** und eine echte Empfangsbestätigung. Ohne Kopplung steht dort ausdrücklich **Website nicht verbunden**. Einmal über den Launcher verbinden; danach erfolgt der Start automatisch. Das Spielfenster nicht minimieren: ein minimiertes Fenster liefert gegebenenfalls keine neuen Bilder. Kurze Verbindungswechsel lassen das letzte Bild stehen, statt schwarz zu blinken; es wird als Wiederverbindung markiert. Auf der Website kann jedes Bild separat neu verbunden werden, ohne das Spiel zu schließen. Bildpakete werden bestätigt; die eingestellte App-FPS bleibt das Ziel, Empfangs-/Anzeige-FPS hängen von Upload und Bildschirm ab. Keine Ton- oder Desktopübertragung.

Ab Version 0.14.3 liest die App bei deutscher SoulSilver alle **20 Sekunden** eine geprüfte Kopie des geladenen Teams und aller Boxen, ohne im Spiel zu speichern. Dafür wird automatisch der in Soul Link enthaltene Emulator gestartet; eine alte, normale melonDS-Auswahl wird beim Update ersetzt. Die Website zeigt den Zeitpunkt des letzten gültigen Live-Stands. Nach dem Start im Spiel **WEITER** wählen; bereits geladene Daten können auch davor verfügbar sein. Unbekannte oder widersprüchliche Daten werden verworfen und ersetzen niemals still das Live-Team durch den letzten Speicherstand. Die Cloud-Sicherung des vollständigen Spielstands benötigt weiterhin reguläres Speichern: Live-Teams sind kein automatisches Speichern. Sehr kurze K.-o.-Zustände zwischen zwei Abfragen können unerkannt bleiben; die Spielregeln müsst ihr weiterhin selbst beachten.

1. Die Windows-ZIP herunterladen und **vollständig entpacken**. SoulLink und die Ordner Emulator und Runtime zusammenlassen.
2. `SoulLink.exe` starten. Die neue App ist noch nicht mit einem kommerziellen Zertifikat signiert. Falls Windows beim ersten Start nachfragt, nur das selbst heruntergeladene SoulLink-Paket freigeben.
3. Eure eigene deutsche **Pokémon SoulSilver-ROM (.nds, Spielcode IPGD)** auswählen. Emulator und Java sind im Download enthalten.
4. **Neue randomisierte Runde erstellen**. Beide Spieler erhalten eigene ROMs und Spielstände in einem neuen Ordner. Die Original-ROM wird nicht verändert.
5. Im Launcher einen der drei Starter auswählen, dann **Anakin starten** (John) oder **Obi-Wan starten** (Eddie). Im Spiel **WEITER** wählen: Ihr steht als männlicher Trainer direkt vor der Auswahl. Pokéball bestätigen und den Starter **T1** nennen.

Standardmäßig werden auch wilde Pokémon und gegnerische Trainerteams zufällig geändert. Die Option kann abgewählt werden: Dann ändern sich nur die Starter und die dazugehörigen Rivalen-Starter. Level, Attacken, Typen und Werte behalten ihre normale Logik; geskriptete Geschenke/statische Begegnungen bleiben unverändert.

## Gemeinsam oder getrennt erstellen

Jede Erstellung erzeugt zwei getrennte Spielerordner. Ihr könnt unabhängig auf euren Rechnern eine Runde erstellen und jeweils euren Spieler starten. Für exakt dieselbe Runde lässt sich der eigene Runden-Ordner zwischen euren Rechnern übertragen. Auf GitHub liegen keine ROM-Dateien. Vorhandene Runden über **Vorhandene Runde öffnen → runde.json** laden. Nach einem App-Neustart wird die letzte Runde wieder angeboten.

## Anakin und Obi-Wan (ab 0.8.0)

Neue Runden enthalten Anakin für John und Obi-Wan für Eddie, mit blauem Lichtschwert. Die Namen im Spiel und Overlay sind **Anakin** und **Obi-Wan**. Alte Ordner-/Dateinamen und interne Spielerkennungen Optimus/Bee bleiben aus Kompatibilitätsgründen erhalten. 45 handgezeichnete Jedi-Designs ersetzen unterstützte Lauf-/Rennfiguren und alle 129 Trainer-Kampfklassen sowie die Kampfrückansichten. Die Figuren sind Pixelgrafiken, keine importierten 3D-Modelle. Trainerpass und Spezialaktionen wie Fahrrad, Surfen und Angeln verwenden vorerst Originalgrafiken. Gegnernamen und Dialoge bleiben unverändert; einige Zivilisten verwenden dieselben Grafikvorlagen wie Trainer.

Für eine bestehende Runde: Spiel speichern, Cloud-Abgleich abwarten, **alle melonDS-Fenster schließen**, Runde öffnen und **Clone Wars: Anakin & Obi-Wan anwenden** bzw. **Figuren aktualisieren** wählen. Eure noch vor der Starter-Auswahl stehenden Spielstände werden umbenannt, nicht zurückgesetzt. Alte Runden mit bereits erhaltenen Pokémon werden bei der Namensmigration sicherheitshalber nicht geändert. Vorherige ROMs liegen als `.pre-jedi.nds`, vorherige Spielstände als `.pre-jedi-name.sav` daneben. Danach **WEITER** wählen, keine neue Runde erstellen. Der vollständige Rundenordner muss für den Gerätewechsel auch die `.graphics-identity.json`-Dateien enthalten, damit die bestehende Cloud-Zuordnung erhalten bleibt. Auf beiden Geräten mindestens 0.8 verwenden.

## Tasten und Einstellungen

Ab 0.4.0 startet das Spiel in **Focus**: großes Spielbild links, kleiner Touchscreen rechts und eine kompakte Leiste unten. **Bild** öffnet interne 3D-Auflösung, Pixel-Skalierung (Scharf/Weich), ganzzahlige Skalierung, Bildschirmlayout und FPS. **Sound** regelt die Lautstärke; **Tasten** öffnet die Belegung. Änderungen im Spiel werden beim regulären Schließen in den Launcher übernommen. Unter **Mehr** bleiben die erweiterten melonDS-Menüs erreichbar. Der Launcher blendet sich während des Spiels aus und kehrt nach dem Schließen zurück.

**Neue Runde** und der andere Spieler oben schließen das aktuelle Spielfenster erst nach Rückfrage. Vorher unbedingt im Spiel speichern: Der Wechsel speichert euren Fortschritt nicht automatisch. Neue Runden erhalten weiterhin einen eigenen Ordner.

Standardtasten: **X = A/Bestätigen**, **Z = B/Zurück**, **S = DS-X/Menü**, **A = DS-Y**, **Pfeile = Bewegen**, **Return = Start**, **Shift = Select**, **Q/W = L/R**, **Tab = Schnelllauf**, **F11 = Vollbild umschalten**. Unter Grafik · Sound · Tasten lassen sich diese Tasten ändern. Im Spiel kann der untere Bildschirm mit der Maus bedient werden.

60 FPS ist normales Spieltempo. 90/120 FPS und unbegrenzt beschleunigen auch Spiel und Ton; das fügt dem Originalspiel keine neuen Animationsbilder hinzu. Die interne Auflösung macht 3D-Flächen schärfer, nicht die ursprünglichen 2D-Sprites. Bei Leistungseinbrüchen 2× oder 1× wählen. Einstellungen gelten ab dem nächsten Spielstart.

**Speichert regelmäßig über SPEICHERN im Spiel.** Speichert vor dem Schließen des Spielfensters. Die mitgelieferten Checkpoints dienen nur neuen Runden und werden nie über einen bestehenden Fortschritt kopiert.

## Zwischen Mac und Windows wechseln (ab 0.6.0)

Einmalig auf beiden Geräten dieselbe aktuelle randomisierte Runde öffnen: den vollständigen Runden-Ordner einschließlich `runde.json`, `.nds`, `.sav` und `.graphics-identity.json` privat auf den zweiten Rechner kopieren. Dort **Vorhandene Runde öffnen** wählen und danach die Website als **derselbe Spieler** verbinden (John = Anakin, Eddie = Obi-Wan). Nicht auf dem zweiten Rechner eine neue Zufallsrunde erzeugen. ROMs werden nicht hochgeladen. Beide Geräte brauchen App-Version 0.8.0 oder neuer für die Jedi-Grafiken und Namen.

Danach läuft der Spielstandabgleich automatisch:

1. Vor dem Spielstart wird die Cloud geprüft und bei eindeutigem Stand die neuere Version geladen. Vor jeder lokalen Ersetzung entsteht eine vollständige Sicherung im Unterordner `Cloud-Sicherungen`.
2. Nach **SPEICHERN im Spiel** wird die `.sav` während des Spiels regelmäßig hochgeladen. Ungespeicherter Fortschritt, Emulator-Savestates, ROMs und Grafikeinstellungen werden nicht synchronisiert.
3. Vor dem Gerätewechsel speichern und das Spielfenster schließen. Den Launcher offen lassen, bis **Cloud gesichert · Gerätewechsel möglich** erscheint. Erst dann auf dem anderen Gerät starten.

**Cloud jetzt abgleichen** erlaubt denselben Abgleich ohne Spielstart. Bei unterschiedlichen Ständen ohne gemeinsame Basis fragt die App nach: **Ja** lädt den Cloud-Stand mit lokaler Sicherung; **Nein** veröffentlicht den lokalen Stand als neue Cloud-Version; **Abbrechen** verändert nichts. Die Cloud hält die letzten zehn unterschiedlichen Spielstände pro Spieler und Website-Runde vor; lokale Sicherungen werden nicht automatisch gelöscht. Bei Verbindungsfehlern bleibt der lokale Stand erhalten; vor dem Wechsel unbedingt erneut abgleichen. Nach einem Absturz kann die Gerätesperre bis zu 90 Sekunden bestehen bleiben.

Gleichzeitiges Spielen **desselben Spielers** auf zwei Geräten wird bei verbundenen aktuellen Apps blockiert. John und Eddie dürfen selbstverständlich gleichzeitig spielen. Eine laufende Sitzung lädt niemals fremde Cloud-Daten über ihren lokalen Spielstand. Alte App-Versionen oder separat gestartete Emulatoren beachten die Cloud-Sperre nicht: deshalb zum Wechseln ausschließlich die aktualisierte SoulLink-App verwenden und alle anderen Emulatorfenster schließen.

## Gemeinsamer Tracker

https://soullink-web-production.up.railway.app

Website mit John (Anakin) oder Eddie (Obi-Wan) und eurem vereinbarten Passwort öffnen. Einer erstellt die gemeinsame Website-Runde; der andere findet nach der Anmeldung dieselbe Runde. In der App im Reiter Gemeinsamer Tracker einmal „Website verbinden“ anklicken und den eigenen Spieler im Browser bestätigen. Danach verbindet sich die App beim Start automatisch; Verbindungsdateien müssen nicht mehr heruntergeladen werden. Die App speichert ihren privaten Zugang nur lokal. Das Website-Passwort ist nicht im Download oder GitHub-Code enthalten.

Ab **0.7.0** folgt die private Bildübertragung der FPS-Einstellung der App: 60, 90, 120 oder unbegrenzt. Änderungen im Spiel werden auch an die Website weitergegeben. Es gibt keine feste Vier-FPS-Bremse mehr. Übertragen werden nur tatsächlich gerenderte DS-Bilder, niemals der Desktop; **kein Ton**, keine Fernsteuerung. Die Website zeigt getrennt die App-Einstellung, empfangene Bilder/s und tatsächlich im Browser gezeichnete Bilder/s. Rechnerleistung, Upload, Browser und Monitor begrenzen die erreichbare Rate; ein 60-Hz-Monitor zeigt keine 120 unterschiedlichen Bilder/s. „Unbegrenzt“ heißt ohne zusätzliches Capture-Limit, nicht unbegrenzt schnelle Übertragung.

Mit „Vorschau an/aus“ lässt sich die Übertragung abschalten. Hohe FPS benötigen mehr Datenvolumen und Upload. Der Encoder und die Übertragung halten nur die jeweils neuesten Bilder, damit langsame Verbindungen keinen wachsenden Rückstau erzeugen. Der Server zeichnet nichts auf und verwirft inaktive Bilder nach wenigen Sekunden. Bei aktivierter Übertragung beim Spielstart läuft das Spiel auch bei Fokuswechsel zum Browser weiter. Hintergrund-Browser-Tabs trennen ihren Empfang; beim Zurückkehren verbinden sie sich neu. Alte App-Versionen liefern weiterhin nur die frühere langsame Vorschau und müssen für hohe Bildraten aktualisiert werden.

Bei einer neuen randomisierten Runde wird die alte Website-Verknüpfung vorsichtshalber gelöst, damit Fänge und Verluste nicht mit der alten Runde vermischt werden. Eine neue Website-Runde anlegen und beide Apps erneut bestätigen. Alte Spielstände und Website-Runden werden nicht gelöscht.

Der Tracker liest ab 0.14.3 das geladene Team und die Boxen alle 20 Sekunden direkt aus dem laufenden Spiel. Namen der Form `T1`, `T2`, … bestimmen das Paar; gleiche Nummern werden verbunden. Fehlt ein älterer Gegenpart, während bereits eine höhere T-Nummer erkannt wurde, wird die Lücke automatisch als gescheiterter Fang markiert. Kurzzeitige K.-o.-Zustände zwischen Abfragen können fehlen. Gesperrte Partner werden im Tracker und in der App angezeigt; ihr müsst eure Soul-Link-Regel weiterhin selbst im Spiel einhalten.

## Plattformen

Version 0.15 wird zunächst nur für Windows 64-Bit Intel/AMD gebaut. Die vorhandene macOS-Version 0.14.4 bleibt separat verfügbar, enthält diese neuen Funktionen aber noch nicht. Ein Windows-Build ersetzt keinen Test auf eurem tatsächlichen PC. Focus ist das angepasste Spielfenster des melonDS-Kerns; der Launcher übernimmt Runden und Tracker.
