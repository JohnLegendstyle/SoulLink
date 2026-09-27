import json
import socket
import struct
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from pathlib import Path
from soullink.frame_receiver import FrameReceiver

class ReceiverTests(unittest.TestCase):
    def test_fragmented_stream_reconnect_and_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'capture.receiver.json';frames=[];done=threading.Event()
            def deliver(packet):
                frames.append(packet)
                if len(frames)==240:done.set()
            receiver=FrameReceiver(path,deliver)
            try:
                config=json.loads(path.read_text());packet=struct.pack('!IHH',4,120,1)+b'\xff\xd8\xff\xd9'
                with socket.create_connection(('127.0.0.1',config['port'])) as bad:bad.sendall(b'x'*64+b'\n')
                for _ in range(2):
                    with socket.create_connection(('127.0.0.1',config['port'])) as client:
                        client.sendall((config['token']+'\n').encode())
                        client.sendall(packet[:3]);client.sendall(packet[3:]+packet*119)
                self.assertTrue(done.wait(3));self.assertEqual(frames,[packet]*240)
            finally:receiver.stop()
            self.assertFalse(path.exists());self.assertFalse(receiver.thread.is_alive())

    def test_mirror_preserves_120fps_across_slow_acknowledgements(self):
        from soullink.online import MirrorWorker
        accepted=[];jpeg=b'\xff\xd8'+b'X'*16000+b'\xff\xd9'
        packet=struct.pack('!IHH',len(jpeg),120,1)+jpeg
        class Connection:
            sock=None
            def __init__(self,*args,**kwargs):pass
            def request(self,method,path,body,headers):self.body=body
            def getresponse(self):
                time.sleep(.3)
                body=self.body;accepted.extend([body[i:i+len(packet)] for i in range(0,len(body),len(packet))])
                class Response:
                    status=200
                    def read(self,size):return json.dumps({'accepted':len(body)//len(packet),'player':'John'}).encode()
                return Response()
            def close(self):pass
        with tempfile.TemporaryDirectory() as directory,patch('soullink.online.http.client.HTTPConnection',Connection):
            frame=Path(directory)/'frame.jpg';frame.with_name('frame.jpg.enabled').touch()
            worker=MirrorWorker({'baseUrl':'http://127.0.0.1:1234','roomId':'test','token':'test','player':'John'},frame,lambda _:None)
            worker.start()
            try:
                descriptor=frame.with_suffix('.receiver.json');deadline=time.monotonic()+3
                while not descriptor.exists() and time.monotonic()<deadline:time.sleep(.005)
                config=json.loads(descriptor.read_text())
                with socket.create_connection(('127.0.0.1',config['port'])) as client:
                    client.sendall((config['token']+'\n').encode());start=time.monotonic()
                    for i in range(240):
                        client.sendall(packet);time.sleep(max(0,start+(i+1)/120-time.monotonic()))
                    deadline=time.monotonic()+2
                    while len(accepted)<240 and time.monotonic()<deadline:time.sleep(.01)
                self.assertEqual(accepted,[packet]*240)
            finally:worker.stop();worker.thread.join(3)
            self.assertFalse(worker.thread.is_alive())
