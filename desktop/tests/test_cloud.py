import base64
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from soullink.cloud import CloudSession, CloudConflict, CloudError, sha

CHECKPOINT = Path(__file__).parents[1] / 'randomizer' / 'checkpoints' / 'Optimus.sav'


class CloudTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.original = CHECKPOINT.read_bytes()
        # Change unused padding only; keeps the actual save and all CRCs valid.
        data = bytearray(self.original); data[-1] ^= 1; self.other = bytes(data)
        self.save = self.root / 'Optimus.sav'; self.save.write_bytes(self.original)
        self.rom = self.root / 'game.nds'; self.rom.write_bytes(b'test-ROM')
        self.current = {'revision': 1, 'sha256': sha(self.original), 'romHash': sha(b'test-ROM')}
        self.download = self.original
        self.uploaded = []
        self.session = CloudSession({'baseUrl': 'http://127.0.0.1:1', 'roomId': 'room', 'player': 'John', 'token': 'token'}, self.save, self.rom, self.root / 'state')
        def api(base, path, method='GET', data=None, token=None, timeout=15):
            if method == 'PUT':
                raw = base64.b64decode(data['data']); self.uploaded.append(raw)
                self.current = {**self.current, 'revision': self.current['revision']+1, 'sha256': sha(raw)}
                self.download = raw
            if 'revision=' in path:
                return {'data': base64.b64encode(self.download).decode()}
            return {'current': self.current}
        self.mock = patch('soullink.cloud.api', side_effect=api).start()
        self.addCleanup(patch.stopall)
        self.addCleanup(self.session.release)
        patch('soullink.cloud.time.sleep').start()

    def baseline(self):
        self.session.prepare()

    def remote_changes(self):
        self.current = {**self.current, 'revision': 2, 'sha256': sha(self.other)}
        self.download = self.other

    def test_equal_first_connection_records_baseline_without_upload(self):
        self.baseline()
        self.assertEqual(self.uploaded, [])
        self.assertEqual(json.loads(self.session.record.read_text())['sha256'], sha(self.original))

    def test_new_cloud_uploads_original(self):
        self.current = {**self.current, 'revision': 0, 'sha256': ''}
        self.baseline()
        self.assertEqual(self.uploaded, [self.original])

    def test_clean_device_downloads_and_backs_up_previous_bytes(self):
        self.baseline(); self.remote_changes(); self.session.prepare()
        self.assertEqual(self.save.read_bytes(), self.other)
        self.assertEqual(next((self.root/'Cloud-Sicherungen').glob('*.sav')).read_bytes(), self.original)

    def test_local_progress_uploads_if_cloud_baseline_unchanged(self):
        self.baseline(); self.save.write_bytes(self.other); self.session.prepare()
        self.assertEqual(self.uploaded, [self.other])

    def test_unknown_different_device_requires_choice(self):
        self.remote_changes()
        with self.assertRaises(CloudConflict): self.session.prepare()
        self.assertEqual(self.save.read_bytes(), self.original)
        self.assertEqual(self.uploaded, [])
        self.session.prepare('cloud')
        self.assertEqual(self.save.read_bytes(), self.other)

    def test_diverged_devices_never_silently_overwrite(self):
        self.baseline(); self.remote_changes()
        local = bytearray(self.original); local[-2] ^= 1; self.save.write_bytes(local)
        with self.assertRaises(CloudConflict): self.session.prepare()
        self.assertEqual(self.save.read_bytes(), bytes(local))
        self.assertEqual(self.uploaded, [])
        self.session.prepare('local')
        self.assertEqual(self.uploaded, [bytes(local)])

    def test_corrupt_download_does_not_replace_local(self):
        self.baseline(); self.remote_changes(); self.download = b'bad'
        with self.assertRaises(CloudError): self.session.prepare()
        self.assertEqual(self.save.read_bytes(), self.original)

    def test_two_local_apps_cannot_lock_same_save(self):
        self.baseline()
        other = CloudSession(self.session.access, self.save, self.rom, self.root/'other')
        with self.assertRaises(CloudError): other.prepare()
        self.session.release(); other.prepare(); other.release()

    def test_failed_upload_does_not_advance_baseline_or_change_local(self):
        self.baseline(); self.save.write_bytes(self.other)
        self.mock.side_effect = OSError('offline')
        with self.assertRaises(CloudError): self.session.upload(self.other)
        self.assertEqual(self.session.last_hash, sha(self.original))
        self.assertEqual(self.save.read_bytes(), self.other)
        self.session.remote_held = False

    def test_stable_snapshot_rejects_wrong_trainer(self):
        self.save.write_bytes(CHECKPOINT.with_name('Bee.sav').read_bytes())
        with self.assertRaises(CloudError): self.session.prepare()
        self.assertEqual(self.uploaded, [])
