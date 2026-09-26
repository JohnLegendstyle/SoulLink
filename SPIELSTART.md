# Soul Link · Optimus und Bee

1. Passende ZIP für Windows oder macOS herunterladen und **vollständig entpacken**. SoulLink und die Ordner Emulator und Runtime zusammenlassen.
2. `SoulLink.exe` (Windows) oder `SoulLink.app` (Mac) starten. Die neue App ist noch nicht mit einem kommerziellen Zertifikat signiert. Falls das Betriebssystem beim ersten Start nachfragt, nur das selbst heruntergeladene SoulLink-Paket freigeben.
3. Eure eigene deutsche **Pokémon SoulSilver-ROM (.nds, Spielcode IPGD)** auswählen. Emulator und Java sind im Download enthalten.
4. **Neue randomisierte Runde erstellen**. Beide Spieler erhalten eigene ROMs und Spielstände in einem neuen Ordner. Die Original-ROM wird nicht verändert.
5. **Optimus starten** oder **Bee starten**. Im Spiel **WEITER** wählen: Ihr steht als männlicher Trainer direkt vor der Starter-Auswahl. Die drei Pokémon wählt ihr selbst. Mindestens eines pro Auswahl ist legendär (einschließlich mysteriöser Pokémon).

Standardmäßig werden auch wilde Pokémon und gegnerische Trainerteams zufällig geändert. Die Option kann abgewählt werden: Dann ändern sich nur die Starter und die dazugehörigen Rivalen-Starter. Level, Attacken, Typen und Werte behalten ihre normale Logik; geskriptete Geschenke/statische Begegnungen bleiben unverändert.

## Gemeinsam oder getrennt erstellen

Jede Erstellung erzeugt zwei getrennte Spielerordner. Ihr könnt unabhängig auf euren Rechnern eine Runde erstellen und jeweils euren Spieler starten. Für exakt dieselbe Runde lässt sich der eigene Runden-Ordner zwischen euren Rechnern übertragen. Auf GitHub liegen keine ROM-Dateien. Vorhandene Runden über **Vorhandene Runde öffnen → runde.json** laden. Nach einem App-Neustart wird die letzte Runde wieder angeboten.

## Optimus Prime und Bumblebee (ab 0.3.0)

Neue Runden enthalten automatisch Optimus Prime für **Optimus** und Bumblebee für **Bee**. Ersetzt werden die Spielfiguren beim Stehen, Gehen und Rennen in allen vier Blickrichtungen, einschließlich des alternativen Laufsets und der Rocket-Verkleidung. Kampfporträts, Trainerpass und Spezialaktionen (z. B. Fahrrad, Surfen und Angeln) verwenden vorerst die Originalgrafiken. Die Namen im Spiel bleiben Optimus und Bee.

Für eine bestehende Runde: Spiel speichern, **alle melonDS-Fenster schließen**, die Runde in SoulLink öffnen und **Optimus Prime & Bumblebee · Figuren aktualisieren** anklicken (auch unter Spiel im Menü). Das verändert ausschließlich die Grafikbereiche der beiden lokalen ROMs. Pokémon, Zufallswerte und `.sav`-Spielstände bleiben unverändert; eine Wiederherstellungskopie endet auf `.pre-transformers.nds`. Danach normal über **WEITER** fortsetzen, keine neue Runde erzeugen. Beim Gerätewechsel auch die aktualisierte `.nds` mitnehmen; Grafikänderungen sind nicht im Spielstand gespeichert.

## Tasten und Einstellungen

Ab 0.4.0 startet das Spiel in **Focus**: großes Spielbild links, kleiner Touchscreen rechts und eine kompakte Leiste unten. **Bild** öffnet interne 3D-Auflösung, Pixel-Skalierung (Scharf/Weich), ganzzahlige Skalierung, Bildschirmlayout und FPS. **Sound** regelt die Lautstärke; **Tasten** öffnet die Belegung. Änderungen im Spiel werden beim regulären Schließen in den Launcher übernommen. Unter **Mehr** bleiben die erweiterten melonDS-Menüs erreichbar. Der Launcher blendet sich während des Spiels aus und kehrt nach dem Schließen zurück.

**Neue Runde** und der andere Spieler oben schließen das aktuelle Spielfenster erst nach Rückfrage. Vorher unbedingt im Spiel speichern: Der Wechsel speichert euren Fortschritt nicht automatisch. Neue Runden erhalten weiterhin einen eigenen Ordner.

Standardtasten: **X = A/Bestätigen**, **Z = B/Zurück**, **S = DS-X/Menü**, **A = DS-Y**, **Pfeile = Bewegen**, **Return = Start**, **Shift = Select**, **Q/W = L/R**, **Tab = Schnelllauf**, **F11 = Vollbild umschalten**. Unter Grafik · Sound · Tasten lassen sich diese Tasten ändern. Im Spiel kann der untere Bildschirm mit der Maus bedient werden.

60 FPS ist normales Spieltempo. 90/120 FPS und unbegrenzt beschleunigen auch Spiel und Ton; das fügt dem Originalspiel keine neuen Animationsbilder hinzu. Die interne Auflösung macht 3D-Flächen schärfer, nicht die ursprünglichen 2D-Sprites. Bei Leistungseinbrüchen 2× oder 1× wählen. Einstellungen gelten ab dem nächsten Spielstart.

**Speichert regelmäßig über SPEICHERN im Spiel.** Speichert vor dem Schließen des Spielfensters. Für einen Gerätewechsel den ganzen Runden-Ordner einschließlich `.sav` kopieren. Die mitgelieferten Checkpoints dienen nur neuen Runden und werden nie über einen bestehenden Fortschritt kopiert.

## Gemeinsamer Tracker

https://soullink-web-production.up.railway.app

Website mit John (Optimus) oder Eddie (Bee) und eurem vereinbarten Passwort öffnen. Einer erstellt die gemeinsame Website-Runde; der andere findet nach der Anmeldung dieselbe Runde. In der App im Reiter Gemeinsamer Tracker einmal „Website verbinden“ anklicken und den eigenen Spieler im Browser bestätigen. Danach verbindet sich die App beim Start automatisch; Verbindungsdateien müssen nicht mehr heruntergeladen werden. Die App speichert ihren privaten Zugang nur lokal. Das Website-Passwort ist nicht im Download oder GitHub-Code enthalten.

Die Bildvorschau zeigt ausschließlich die beiden DS-Bildschirme, niemals euren Desktop. Bis zu vier Bilder pro Sekunde, ohne Ton und ohne Fernsteuerung. Im Spielfenster lässt sie sich mit „Vorschau an/aus“ umschalten; die Auswahl bleibt beim Beenden erhalten. Es gibt keine Aufzeichnung: Der Server hält nur das neueste Bild je Spieler im Arbeitsspeicher und verwirft es nach wenigen Sekunden ohne neue Übertragung. Die Vorschau kann abhängig von Rechner und Internetverbindung langsamer sein. Das eigentliche Spiel läuft lokal weiter.

Bei einer neuen randomisierten Runde wird die alte Website-Verknüpfung vorsichtshalber gelöst, damit Fänge und Verluste nicht mit der alten Runde vermischt werden. Eine neue Website-Runde anlegen und beide Apps erneut bestätigen. Alte Spielstände und Website-Runden werden nicht gelöscht.

Der Tracker liest **gespeicherte Spielstände**, keine flüchtigen Kampfdaten. Änderungen erscheinen nach dem Speichern. Ein K. o. wird nur erkannt, wenn mit 0 KP gespeichert wurde. Paare entstehen nach der Reihenfolge erstmals gespeicherter Fänge. Gesperrte Partner werden im Tracker und in der App angezeigt; ihr müsst eure Soul-Link-Regel selbst im Spiel einhalten.

## Plattformen

Windows-Paket: 64-Bit Intel/AMD. Mac-Paket: Apple Silicon (M1 oder neuer), macOS 14 oder neuer. Ein Windows-Build ersetzt keinen Test auf eurem tatsächlichen PC. Focus ist das angepasste Spielfenster des melonDS-Kerns; der Launcher übernimmt Runden und Tracker.
