import json
import socket
import struct
import tempfile
import threading
import unittest
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
