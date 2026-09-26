"""Versioned .sav handoff. Never downloads while the emulator is running."""
from __future__ import annotations
import base64
import hashlib
import json
import os
import secrets
import threading
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from .online import api
from .save_reader import parse_save


class CloudError(RuntimeError):
    pass


class CloudConflict(CloudError):
    pass


def sha(data):
    return hashlib.sha256(data).hexdigest()


def atomic_write(path: Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.' + secrets.token_hex(8) + '.tmp')
    try:
        with temporary.open('xb') as stream:
            if os.name != 'nt': os.chmod(temporary, 0o600)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


class CloudSession:
    def __init__(self, access, save: Path, rom: Path, state_dir: Path, on_status=lambda text: None):
        self.access, self.save, self.rom = access, save, rom
        self.on_status = on_status
        self.lease = secrets.token_hex(32)
        self.rom_hash = ''
        identity = access['roomId'] + ':' + access['player'] + ':' + str(save.resolve())
        self.record = state_dir / (sha(identity.encode()) + '.json')
        self.revision = 0
        self.last_hash = ''
        self.remote_held = False
        self.lock = None
        self.stop_event = threading.Event()
        self.thread = None
        self.failed = False

    def request(self, suffix='', method='GET', data=None):
        path = '/api/cloud-save' + suffix + '?' + urlencode({'id': self.access['roomId']})
        try:
            return api(self.access['baseUrl'], path, method, data, self.access['token'], timeout=15)
        except HTTPError as error:
            try: detail = json.load(error).get('error', 'Cloud-Abgleich abgelehnt.')
            except (ValueError, OSError): detail = 'Cloud-Abgleich abgelehnt.'
            raise CloudError(detail) from None
        except (OSError, ValueError) as error:
            raise CloudError('Cloud nicht erreichbar. Dein lokaler Stand bleibt erhalten. Bitte später erneut versuchen.') from error

    def payload(self, **extra):
        return {'romHash': self.rom_hash, 'lease': self.lease, **extra}

    def acquire_local(self):
        if self.lock: return
        lock = self.save.with_name(self.save.name + '.soullink-lock').open('a+b')
        try:
            if os.name == 'nt':
                import msvcrt
                if lock.tell() == 0: lock.write(b'0'); lock.flush()
                lock.seek(0); msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            lock.close()
            raise CloudError('Dieser Spielstand ist bereits in einer anderen SoulLink-App geöffnet.') from None
        self.lock = lock

    def snapshot(self):
        first = self.save.read_bytes()
        time.sleep(.3)
        second = self.save.read_bytes()
        if first != second: raise CloudError('Das Spiel speichert gerade. Bitte gleich erneut versuchen.')
        state = parse_save(second)
        from .identity import allowed_names
        if state.trainer not in allowed_names(self.access['player']): raise CloudError('Der Spielstand gehört zum anderen Trainer.')
        return second

    def remember(self, current):
        self.revision, self.last_hash = current['revision'], current['sha256']
        atomic_write(self.record, json.dumps({'romHash': self.rom_hash,
                     'sha256': self.last_hash, 'revision': self.revision}).encode())

    def upload(self, data):
        result = self.request(method='PUT', data=self.payload(
            baseRevision=self.revision, data=base64.b64encode(data).decode()))
        current = result['current']
        if current['sha256'] != sha(data): raise CloudError('Die Cloud-Prüfsumme stimmt nicht überein.')
        self.remember(current)
        self.on_status('Cloud gesichert · Version ' + str(self.revision))

    def download(self, current, previous):
        # Download a fixed immutable revision, not a potentially changing "latest" file.
        path = '/api/cloud-save?' + urlencode({'id': self.access['roomId'], 'revision': current['revision']})
        result = api(self.access['baseUrl'], path, token=self.access['token'], timeout=15)
        data = base64.b64decode(result['data'], validate=True)
        from .identity import allowed_names
        if sha(data) != current['sha256'] or parse_save(data).trainer not in allowed_names(self.access['player']):
            raise CloudError('Die heruntergeladene Sicherung ist ungültig. Lokaler Stand bleibt erhalten.')
        if self.save.read_bytes() != previous:
            raise CloudError('Der lokale Spielstand wurde inzwischen geändert. Bitte alle anderen Emulatoren schließen.')
        backup = self.save.parent / 'Cloud-Sicherungen' / (self.save.stem + '-' + time.strftime('%Y%m%d-%H%M%S') + '-' + secrets.token_hex(4) + '.sav')
        atomic_write(backup, previous)
        atomic_write(self.save, data)
        self.remember(current)
        self.on_status('Cloud geladen · vorheriger Stand in Cloud-Sicherungen gesichert')

    def prepare(self, choice=None):
        self.acquire_local()
        if not self.rom_hash:
            from .jedi import rom_identity
            self.rom_hash = rom_identity(self.rom)
        local = self.snapshot()
        current = self.request('/lease', 'POST', self.payload())['current']
        self.remote_held = True
        local_hash = sha(local)
        self.revision = current['revision']
        try: baseline = json.loads(self.record.read_text())
        except (OSError, ValueError): baseline = {}
        if not current['revision']:
            self.upload(local)
        elif current['sha256'] == local_hash:
            self.remember(current)
        elif choice == 'cloud':
            self.download(current, local)
        elif choice == 'local':
            self.upload(local)
        elif baseline.get('romHash') == self.rom_hash and baseline.get('sha256') == local_hash:
            self.download(current, local)
        elif baseline.get('romHash') == self.rom_hash and baseline.get('sha256') == current['sha256']:
            self.upload(local)
        else:
            raise CloudConflict('Auf diesem Gerät und in der Cloud liegen unterschiedliche Spielstände.\n'
                                'Keiner wurde überschrieben. Welche Version möchtest du fortsetzen?')
        self.on_status('Cloud bereit · Version ' + str(self.revision))

    def flush(self):
        self.request('/lease', 'POST', self.payload())
        data = self.snapshot()
        if sha(data) != self.last_hash: self.upload(data)

    def start(self):
        def run():
            renewed = time.monotonic()
            while not self.stop_event.wait(3):
                try:
                    if time.monotonic() - renewed > 25:
                        self.request('/lease', 'POST', self.payload()); renewed = time.monotonic()
                    data = self.snapshot()
                    if sha(data) != self.last_hash: self.upload(data)
                    self.failed = False
                except Exception:
                    self.failed = True
                    self.on_status('Cloud wartet · lokal sicher. Vor dem Gerätewechsel Spiel schließen und Abgleich abwarten.')
        self.thread = threading.Thread(target=run, daemon=True)
        self.thread.start()

    def release(self):
        try:
            if self.remote_held: self.request('/lease', 'POST', self.payload(release=True))
        finally:
            self.remote_held = False
            if self.lock:
                if os.name == 'nt':
                    import msvcrt
                    self.lock.seek(0); msvcrt.locking(self.lock.fileno(), msvcrt.LK_UNLCK, 1)
                self.lock.close(); self.lock = None

    def finish(self):
        self.stop_event.set()
        if self.thread: self.thread.join()
        try:
            self.flush()
            self.on_status('Cloud gesichert · Gerätewechsel möglich')
        finally:
            self.release()
