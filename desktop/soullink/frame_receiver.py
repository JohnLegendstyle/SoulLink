"""Authenticated loopback-only capture pipe; no per-frame filesystem polling."""
import hmac
import json
import secrets
import socket
import threading
import time
from .cloud import atomic_write

class FrameReceiver:
    def __init__(self, descriptor, deliver):
        self.descriptor=descriptor;self.deliver=deliver;self.secret=secrets.token_hex(32)
        self.stop_event=threading.Event();self.last_frame=0.;self.client=None
        self.server=socket.socket();self.server.bind(('127.0.0.1',0));self.server.listen(2);self.server.settimeout(.25)
        try:atomic_write(descriptor,json.dumps({'port':self.server.getsockname()[1],'token':self.secret}).encode())
        except Exception:self.server.close();raise
        self.thread=threading.Thread(target=self.run,daemon=True);self.thread.start()
    def exact(self,connection,size):
        data=bytearray()
        while len(data)<size and not self.stop_event.is_set():
            part=connection.recv(size-len(data))
            if not part:raise OSError('Capture disconnected')
            data.extend(part)
        if len(data)!=size:raise OSError('Capture stopped')
        return bytes(data)
    def run(self):
        while not self.stop_event.is_set():
            try:
                client,_=self.server.accept();self.client=client
                with client:
                    client.settimeout(1);client.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
                    if not hmac.compare_digest(self.exact(client,65),(self.secret+'\n').encode()):continue
                    while not self.stop_event.is_set():
                        header=self.exact(client,8);size=int.from_bytes(header[:4],'big')
                        if not 4<=size<=300000:raise ValueError('Invalid capture size')
                        self.deliver(header+self.exact(client,size));self.last_frame=time.monotonic()
            except (OSError,ValueError):pass
            finally:self.client=None
    def stop(self):
        self.stop_event.set();self.server.close()
        if self.client:
            try:self.client.shutdown(socket.SHUT_RDWR)
            except OSError:pass
        self.thread.join(timeout=2)
        try:
            if json.loads(self.descriptor.read_text()).get('token')==self.secret:self.descriptor.unlink()
        except (OSError,ValueError):pass
