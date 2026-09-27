# Veröffentlichungsablauf

Nummerierte Releases sind die stabilen Downloads. `spielabend` ist ausschließlich der überschreibbare Build-Kanal der bestehenden GitHub Action; dessen automatisch erzeugter Titel ist keine Versionsangabe.

Für jede neue stabile Desktop-Version:

1. Versionsnummer in `desktop/soullink/__init__.py` und `desktop/SoulLink.spec` aktualisieren.
2. `releases/vX.Y.Z.md` mit Änderungen, Plattformen, sicheren Update-Schritten, Einschränkungen und dem geprüften Quellstand anlegen. README und CHANGELOG aktualisieren.
3. Desktop-Build vollständig abwarten: Windows, macOS und Release-Job müssen erfolgreich sein. Die Paketierung führt auf beiden Systemen den App-Selbsttest aus.
4. `python3 scripts/publish-version.py X.Y.Z BUILD_RUN_ID` ausführen. Das Skript prüft Buildstatus, Quellversion, Zuordnung des fortlaufenden Downloads zum Build, Dateigröße, GitHub-SHA256 und ZIP-Integrität. Es verwendet die vorhandene Git-Anmeldung, ohne Zugangsdaten auszugeben oder zu speichern.
5. Erst nach vollständigem Upload aller Dateien wird der Entwurf als stabiler Release veröffentlicht. Existierende veröffentlichte Versionspakete werden niemals überschrieben. Unterbrochene Entwürfe lassen sich mit demselben Aufruf fortsetzen.
6. `/releases/latest`, beide Plattformdownloads, Release-Notizen und Prüfsummen nach der Veröffentlichung kontrollieren. Dokumentationsänderungen mit `[skip ci]` veröffentlichen, wenn kein neuer App-Build benötigt wird.

Ältere Zwischenstände nicht mit aktuellen Paketen nachträglich auffüllen. Alte Archive bleiben unverändert. Website-Updates werden separat dokumentiert und erhalten nicht automatisch eine neue Desktop-Versionsnummer.

Die bestehende Action erzeugt weiterhin den fortlaufenden Build. Die stabile Veröffentlichung ist bewusst ein eigener, geprüfter Schritt mit dem oben genannten Skript; sie erfolgt nicht automatisch bei jedem Commit.
