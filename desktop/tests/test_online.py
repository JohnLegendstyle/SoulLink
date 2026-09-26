import tempfile
import unittest
import struct
from pathlib import Path
from unittest.mock import patch,Mock
from soullink.online import WEBSITE,browser_url,trusted_base,pairing,MirrorWorker

class OnlineTests(unittest.TestCase):
    def test_pairing_keeps_device_secret_out_of_browser(self):
        opened=[];connected=[];status=[]
        stop=Mock();stop.wait.return_value=False
        access={'player':'John','roomId':'room','token':'private-player','readToken':'private-read'}
        with patch('soullink.online.api',side_effect=[{'id':'device','secret':'private-device'}, {'status':'approved','access':access}]) as api:
            pairing(opened.append,connected.append,status.append,stop)
        self.assertEqual(opened,[WEBSITE+'/#pair=device'])
        self.assertEqual(connected[0]['token'],'private-player')
        self.assertEqual(api.call_args.kwargs['token'],'private-device')
    def test_website_links_never_contain_player_write_token(self):
        link=browser_url({'baseUrl':WEBSITE,'roomId':'room','readToken':'read','token':'write-secret'})
        self.assertIn('#room=room&key=read',link)
        self.assertNotIn('write-secret',link)
    def test_untrusted_endpoint_rejected(self):
        for url in ('https://example.org','http://example.org','https://soullink-web-production.up.railway.app.evil.org','http://user@127.0.0.1:3000'):
            with self.assertRaises(ValueError):trusted_base(url)
        self.assertEqual(trusted_base('http://127.0.0.1:3000'),'http://127.0.0.1:3000')
    def test_stop_disables_capture(self):
        with tempfile.TemporaryDirectory() as temp:
            frame=Path(temp)/'frame.jpg';flag=Path(temp)/'frame.jpg.enabled';flag.touch()
            worker=MirrorWorker({},frame,lambda text:None);worker.stop()
            self.assertTrue(worker.stop_event.is_set());self.assertFalse(flag.exists())
    def test_native_packet_carries_fps_without_audio(self):
        jpeg=b'\xff\xd8\xff\xd9'
        for fps in (0,60,90,120):
            data=struct.pack('!IHH',len(jpeg),fps,1)+jpeg
            self.assertEqual(MirrorWorker.packet(data),(data,fps))
        legacy,fps=MirrorWorker.packet(jpeg)
        self.assertEqual(fps,4);self.assertEqual(legacy[8:],jpeg)
    def test_native_packet_rejects_oversized_truncated_and_invalid_data(self):
        for data in (b'bad',struct.pack('!IHH',4,120,2)+b'\xff\xd8\xff\xd9',struct.pack('!IHH',999,120,1)+b'\xff\xd8\xff\xd9',struct.pack('!IHH',4,1001,1)+b'\xff\xd8\xff\xd9'):
            with self.assertRaises(ValueError):MirrorWorker.packet(data)
