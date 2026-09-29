from __future__ import annotations

import json
import threading
import time
import urllib.error
import urllib.request
import uuid
import ssl
from pathlib import Path
from typing import Callable

from .save_reader import read_save

TEAM_REFRESH_SECONDS = 20


def team_refresh_due(now: float, last_attempt: float | None) -> bool:
    return last_attempt is None or now - last_attempt >= TEAM_REFRESH_SECONDS


def tls_context() -> ssl.SSLContext:
    import certifi
    return ssl.create_default_context(cafile=certifi.where())


class SyncWorker:
    def __init__(self, connection: Path, save: Path, on_status: Callable[[str], None], team: Path | None = None, position: Path | None = None):
        self.connection = connection
        self.save = save
        self.team = team
        self.position = position
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
            context = tls_context()
            last_team_attempt = None
            last_state = None
            last_live = False
            waiting_for_live = bool(self.team)
            live_problem = ''
            while not self.stop_event.is_set():
                position=None
                if self.position:
                    try:
                        from .live_position import read_position
                        position=read_position(self.position)
                    except (OSError,ValueError):pass
                full=team_refresh_due(time.monotonic(),last_team_attempt)
                live=False;state=None
                sent_full=False
                if full:
                    last_team_attempt=time.monotonic()
                    try:
                        state=read_save(self.save)
                    except (OSError,ValueError):
                        self.on_status('Warte auf einen vollständig gespeicherten Spielstand …')
                        self.stop_event.wait(1)
                        continue
                    if self.team:
                        try:
                            from .live_team import read_team
                            state=read_team(self.team,state);live=True
                            waiting_for_live=False
                            live_problem=''
                        except (OSError,ValueError) as error:
                            # When a live feed is expected, never overwrite it
                            # with the last cartridge save. Keep the prior live
                            # team visible and retry on the fixed clock.
                            waiting_for_live=True
                            live_problem=str(error)
                            state=None
                    if state is not None:
                        self.fainted.update(p.uid for p in state.party if p.hp == 0)
                        payload={"roomId":access["roomId"],"sessionId":self.session,"sequence":self.sequence,
                                 "party":[p.api() for p in state.party],"owned":[p.api() for p in state.owned],
                                 "fainted":sorted(self.fainted),"teamSource":"live" if live else "save",
                                 "teamCapturedAt":int((self.team if live else self.save).stat().st_mtime*1000)}
                        sent_full=True
                    else:
                        payload={"roomId":access["roomId"],"heartbeat":True}
                else:
                    payload={"roomId":access["roomId"],"heartbeat":True}
                if position:payload['position']=position
                request = urllib.request.Request(
                    endpoint, data=json.dumps(payload).encode(), method="POST",
                    headers={"Authorization": "Bearer " + access["token"], "Content-Type": "application/json"},
                )
                try:
                    with urllib.request.urlopen(request, timeout=10, context=context) as response:
                        result = json.loads(response.read())
                except (OSError,ValueError,urllib.error.URLError):
                    self.on_status('Verbindung unterbrochen. Neuer Versuch in wenigen Sekunden …')
                    self.stop_event.wait(5)
                    continue
                if sent_full:
                    self.sequence += 1
                    last_state=state
                    last_live=live
                else:
                    state=last_state
                    live=last_live
                partner = "Partner online" if result.get("partnerOnline") else "Partner nicht verbunden"
                blocked = set(result.get('blocked',[]))
                locked = [p.nickname or f'Pokémon #{p.species}' for p in state.party if p.uid in blocked] if state else []
                notice = ' · GESPERRT: ' + ', '.join(locked) if locked else ''
                location=' · Position live' if position else ''
                tracker=('Live-Team · alle 20 Sekunden' if last_live and not waiting_for_live
                         else 'Live-Team wartet: '+live_problem if live_problem
                         else 'Live-Team wartet auf den nächsten 20-Sekunden-Stand' if last_live
                         else 'Live-Team wird vorbereitet · nicht der letzte Speicherstand' if self.team
                         else 'Tracker verbunden')
                self.on_status(f"{tracker}{location} · {partner}{notice}")
                self.stop_event.wait(1)
        except (OSError, ValueError, KeyError, urllib.error.URLError) as error:
            self.on_status(f"Synchronisierung pausiert: {error}")
