import hashlib
import io
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch
from unittest.mock import Mock
from types import SimpleNamespace
import zipfile
from soullink import updater as u

class UpdaterTests(unittest.TestCase):
    def release(self):
        name='SoulLink-0.11.0-Windows-x64.zip'
        return {'tag_name':'v0.11.0','assets':[{'name':name,'size':10,'digest':'sha256:'+'a'*64,'browser_download_url':f'{u.REPO}/releases/download/v0.11.0/{name}'}]}

    def test_versions_and_platforms(self):
        self.assertGreater(u.version_tuple('0.11.0'),u.version_tuple('0.9.0'))
        self.assertEqual(u.platform_label('Windows','AMD64'),'Windows-x64')
        self.assertEqual(u.platform_label('Darwin','arm64'),'macOS-arm64')
        for system,machine in [('Darwin','x86_64'),('Linux','x86_64')]:
            with self.assertRaises(ValueError):u.platform_label(system,machine)
        with self.assertRaises(ValueError):u.version_tuple('v0.11.0-beta')

    def test_only_newer_stable_exact_asset(self):
        data=self.release()
        self.assertEqual(u.release_info(data,'0.10.0','Windows-x64')['version'],'0.11.0')
        self.assertIsNone(u.release_info(data,'0.11.0','Windows-x64'))
        self.assertIsNone(u.release_info(data,'0.12.0','Windows-x64'))
        for field,value in [('digest',''),('browser_download_url','https://example.com/evil.zip'),('size',u.LIMIT+1)]:
            data=self.release();data['assets'][0][field]=value
            with self.assertRaises(ValueError):u.release_info(data,'0.10.0','Windows-x64')
        data=self.release();data['prerelease']=True
        with self.assertRaises(ValueError):u.release_info(data,'0.10.0','Windows-x64')

    def archive(self, entries):
        buf=io.BytesIO()
        with zipfile.ZipFile(buf,'w') as z:
            for name,value in entries:z.writestr(name,value)
        return buf.getvalue()

    def test_extract_and_preserve_unrelated_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);save=root/'round.sav';save.write_bytes(b'precious')
            z=root/'update.zip';z.write_bytes(self.archive([('SoulLink-Windows-x64/SoulLink.exe',b'app')]))
            app=u.extract(z,root/'stage','Windows-x64')
            self.assertEqual(app.read_bytes(),b'app');self.assertEqual(save.read_bytes(),b'precious')

    def test_bad_paths_and_duplicates(self):
        for name in ['../escape','/escape','SoulLink-Windows-x64/../../escape','SoulLink-Windows-x64/C:evil','SoulLink-Windows-x64/a\\b']:
            with self.subTest(name=name),tempfile.TemporaryDirectory() as tmp:
                z=Path(tmp)/'x.zip';z.write_bytes(self.archive([(name,b'bad')]))
                with self.assertRaises(ValueError):u.extract(z,Path(tmp)/'stage','Windows-x64')
        with tempfile.TemporaryDirectory() as tmp:
            z=Path(tmp)/'x.zip';z.write_bytes(self.archive([('SoulLink-Windows-x64/A',b'a'),('SoulLink-Windows-x64/a',b'b')]))
            with self.assertRaises(ValueError):u.extract(z,Path(tmp)/'stage','Windows-x64')

    def test_symlink_escape_rejected_and_mac_modes_preserved(self):
        for target in ['/tmp/outside','../../outside']:
            with tempfile.TemporaryDirectory() as tmp:
                item=zipfile.ZipInfo('SoulLink-macOS-arm64/escape');item.external_attr=(stat.S_IFLNK|0o777)<<16
                z=Path(tmp)/'x.zip';z.write_bytes(self.archive([(item,target)]))
                with self.assertRaises(ValueError):u.extract(z,Path(tmp)/'stage','macOS-arm64')
        if os.name=='nt':return  # macOS symlink preservation is exercised on the macOS runner.
        with tempfile.TemporaryDirectory() as tmp:
            item=zipfile.ZipInfo('SoulLink-macOS-arm64/SoulLink.app/Contents/MacOS/SoulLink');item.external_attr=(stat.S_IFREG|0o755)<<16
            link=zipfile.ZipInfo('SoulLink-macOS-arm64/alias');link.external_attr=(stat.S_IFLNK|0o777)<<16
            z=Path(tmp)/'x.zip';z.write_bytes(self.archive([(item,b'app'),(link,'SoulLink.app')]))
            app=u.extract(z,Path(tmp)/'stage','macOS-arm64')
            self.assertTrue(app.is_dir())
            self.assertTrue((app.parent/'alias').is_symlink())

    def test_verified_download_and_failure_cleanup(self):
        payload=self.archive([('SoulLink-Windows-x64/SoulLink.exe',b'app')])
        info=dict(version='0.11.0',url=u.REPO+'/test',sha256=hashlib.sha256(payload).hexdigest(),size=len(payload),label='Windows-x64')
        def response(*args,**kwargs):
            stream=io.BytesIO(payload);stream.url='https://release-assets.githubusercontent.com/test';return stream
        with tempfile.TemporaryDirectory() as tmp,patch.object(u.urllib.request,'urlopen',response):
            root=Path(tmp)
            app=u.prepare(info,root);self.assertEqual(app.read_bytes(),b'app')
            previous=set(root.iterdir());info['sha256']='0'*64
            with self.assertRaises(ValueError):u.prepare(info,root)
            self.assertEqual(set(root.iterdir()),previous)

    def test_switch_blocked_by_game_cloud_and_other_work(self):
        from soullink.app import SoulLinkApp
        for pending,session,running in [(True,None,False),(False,object(),False),(False,None,True)]:
            app=SimpleNamespace(cloud_pending=pending,cloud_session=session,
                processes={'player':Mock(poll=Mock(return_value=None if running else 0))})
            with patch('soullink.app.messagebox.showinfo'):
                self.assertTrue(SoulLinkApp.cloud_busy(app))
        for busy,creating,pairing in [(True,False,False),(False,True,False),(False,False,True)]:
            app=SimpleNamespace(update_ready=Path('/not-started'),update_busy=False,
                cloud_busy=lambda:busy,creating=creating,pairing_active=pairing)
            with patch('soullink.app.messagebox.showinfo'),patch('soullink.app.subprocess.Popen') as start,patch('soullink.app.messagebox.askyesno') as confirm:
                SoulLinkApp.activate_update(app)
                start.assert_not_called();confirm.assert_not_called()

if __name__=='__main__':unittest.main()
