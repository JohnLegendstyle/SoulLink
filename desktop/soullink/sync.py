from __future__ import annotations

import json
import threading
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Callable

from .save_reader import read_save


class SyncWorker:
    def __init__(self, connection: Path, save: Path, on_status: Callable[[str], None]):
        self.connection = connection
        self.save = save
        self.on_status = on_status
        self.stop_event = threading.Event()
        self.thread: threading.Thread | None = None
        self.session = uuid.uuid4().hex
        self.sequence = 0
        self.fainted: set[str] = set()

    def start(self) -> None:
        if self.thread and self.thread.is_alive():
            return
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.stop_event.set()

    def _run(self) -> None:
        try:
            access = json.loads(self.connection.read_text(encoding="utf-8"))
            endpoint = access["baseUrl"].rstrip("/") + "/api/sync"
            if not endpoint.startswith('https://') and not endpoint.startswith('http://127.0.0.1:'):
                raise ValueError('Die Verbindungsadresse muss HTTPS verwenden.')
            while not self.stop_event.is_set():
                try:
                    state = read_save(self.save)
                except (OSError,ValueError):
                    self.on_status('Warte auf einen vollständig gespeicherten Spielstand …')
                    self.stop_event.wait(2)
                    continue
                self.fainted.update(p.uid for p in state.party if p.hp == 0)
                payload = {
                    "roomId": access["roomId"], "sessionId": self.session,
                    "sequence": self.sequence, "party": [p.api() for p in state.party],
                    "owned": [p.api() for p in state.owned], "fainted": sorted(self.fainted),
                }
                request = urllib.request.Request(
                    endpoint, data=json.dumps(payload).encode(), method="POST",
                    headers={"Authorization": "Bearer " + access["token"], "Content-Type": "application/json"},
                )
                try:
                    with urllib.request.urlopen(request, timeout=10) as response:
                        result = json.loads(response.read())
                except (OSError,ValueError,urllib.error.URLError):
                    self.on_status('Verbindung unterbrochen. Neuer Versuch in wenigen Sekunden …')
                    self.stop_event.wait(5)
                    continue
                self.sequence += 1
                partner = "Partner online" if result.get("partnerOnline") else "Partner nicht verbunden"
                blocked = set(result.get('blocked',[]))
                locked = [p.nickname or f'Pokémon #{p.species}' for p in state.party if p.uid in blocked]
                notice = ' · GESPERRT: ' + ', '.join(locked) if locked else ''
                self.on_status(f"Spielstand synchronisiert · {partner}{notice}")
                self.stop_event.wait(2)
        except (OSError, ValueError, KeyError, urllib.error.URLError) as error:
            self.on_status(f"Synchronisierung pausiert: {error}")
