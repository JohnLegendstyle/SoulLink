"""Browser-confirmed pairing and a latest-only private game preview."""
from pathlib import Path
import json
import threading
import time
import http.client
import os
import socket
import struct
from collections import deque
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen
from .sync import tls_context

WEBSITE='https://soullink-web-production.up.railway.app'

def trusted_base(base):
    parsed=urlsplit(base)
    if base!=WEBSITE and not (parsed.scheme=='http' and parsed.hostname=='127.0.0.1' and not parsed.username and parsed.path in ('','/')):
        raise ValueError('Unbekannte Website-Adresse.')
    return base.rstrip('/')

def api(base,path,method='GET',data=None,token=None,timeout=10):
    headers={'Content-Type':'application/json'}
    if token: headers['Authorization']='Bearer '+token
    request=Request(trusted_base(base)+path,method=method,headers=headers,
                    data=json.dumps(data).encode() if data is not None else None)
    with urlopen(request,timeout=timeout,context=tls_context()) as response: return json.load(response)

def browser_url(access):
    return trusted_base(access['baseUrl'])+'/#'+urlencode({'room':access['roomId'],'key':access['readToken']})

def pairing(on_open,on_done,on_status,stop,base=WEBSITE):
    try:
        grant=api(base,'/api/pair','POST',{})
        on_open(base+'/#'+urlencode({'pair':grant['id']}))
        on_status('Bitte im Browser John (Anakin) oder Eddie (Obi-Wan) bestätigen. Danach verbindet sich die App automatisch.')
        deadline=time.monotonic()+300
        while not stop.wait(2) and time.monotonic()<deadline:
            result=api(base,'/api/pair?'+urlencode({'id':grant['id']}),token=grant['secret'])
            if result['status']=='approved':
                access=result['access']
                if access['player'] not in ('John','Eddie'): raise ValueError('Unbekannter Spieler.')
                on_done({**access,'baseUrl':base});return
        if not stop.is_set(): on_status('Bestätigung abgelaufen. Bitte Website verbinden erneut anklicken.')
    except Exception:
        on_status('Website-Verbindung nicht möglich. Bitte erneut versuchen; das Spiel läuft unabhängig weiter.')

class MirrorWorker:
    def __init__(self,access,frame:Path,on_status):
        self.access=access;self.frame=frame;self.on_status=on_status
        self.stop_event=threading.Event();self.thread=None
        self.connection=None
        self.frames=deque();self.frames_lock=threading.Lock()
    def start(self):
        self.thread=threading.Thread(target=self._run,daemon=True);self.thread.start()
    def stop(self):
        self.stop_event.set()
        self.frame.with_name(self.frame.name+'.enabled').unlink(missing_ok=True)
        self._disconnect()
    def _disconnect(self):
        connection=self.connection;self.connection=None
        if connection:
            try:
                if connection.sock: connection.sock.shutdown(socket.SHUT_RDWR)
            except OSError: pass
            connection.close()
    @staticmethod
    def packet(data):
        # Compatibility for an older native panel; report its real four-FPS cap.
        if data.startswith(b'\xff\xd8') and data.endswith(b'\xff\xd9') and len(data)<=300000:
            return struct.pack('!IHH',len(data),4,1)+data,4
        if len(data)<12: raise ValueError('Invalid frame')
        size,fps,kind=struct.unpack('!IHH',data[:8])
        if size!=len(data)-8 or size>300000 or fps>1000 or kind!=1 or data[8:10]!=b'\xff\xd8' or data[-2:]!=b'\xff\xd9':
            raise ValueError('Invalid frame')
        return data,fps
    def _run(self):
        """Collect at native FPS; send bounded batches and wait for real ACKs."""
        from .cloud import atomic_write
        base=urlsplit(trusted_base(self.access['baseUrl']))
        endpoint='/api/live/batch?'+urlencode({'id':self.access['roomId']})
        status_path=self.frame.with_suffix('.status.json')
        reconnect=self.frame.with_suffix('.reconnect')
        flag=self.frame.with_name(self.frame.name+'.enabled')
        status='';captured=0;last_capture=0.;capture_error=False
        def deliver(data):
            nonlocal captured,last_capture,capture_error
            packet,fps=self.packet(data);last_capture=time.monotonic();captured=fps;capture_error=False
            with self.frames_lock:
                self.frames.append((packet,last_capture))
                while len(self.frames)>96 or sum(len(p[0]) for p in self.frames)>8000000:self.frames.popleft()
        from .frame_receiver import FrameReceiver
        try:receiver=FrameReceiver(self.frame.with_suffix('.receiver.json'),deliver)
        except OSError:
            self.on_status('Bildleitung konnte nicht gestartet werden. Übertragung erneut starten.');return
        def report(message,live=False):
            nonlocal status
            try:atomic_write(status_path,json.dumps({'message':message,'live':live,'at':time.time()}).encode())
            except OSError:pass # Windows can briefly hold the native status reader.
            if message!=status:status=message;self.on_status(message)
        def collect():
            nonlocal captured,last_capture,capture_error
            last=None
            while not self.stop_event.wait(.002):
                if not flag.exists():
                    with self.frames_lock:self.frames.clear()
                    last=None;self.stop_event.wait(.1);continue
                if time.monotonic()-receiver.last_frame<1:continue
                try:
                    stat=self.frame.stat()
                    if stat.st_mtime_ns==last or time.time()-stat.st_mtime>3:continue
                    deliver(self.frame.read_bytes());last=stat.st_mtime_ns
                except FileNotFoundError:pass
                except (OSError,ValueError):capture_error=True
        timer=None
        if os.name=='nt':
            import ctypes
            timer=ctypes.windll.winmm;timer.timeBeginPeriod(1)
        collector=threading.Thread(target=collect,daemon=True);collector.start()
        try:
            next_send=0.
            while not self.stop_event.wait(max(.001,next_send-time.monotonic())):
                next_send=time.monotonic()+.04
                if not flag.exists():
                    self._disconnect();report('Übertragung ausgeschaltet');self.stop_event.wait(.4);continue
                if reconnect.exists():reconnect.unlink(missing_ok=True);self._disconnect()
                with self.frames_lock:
                    now=time.monotonic()
                    fresh=[];size=0
                    while self.frames and now-self.frames[0][1]>.75:self.frames.popleft()
                    while self.frames and len(fresh)<64 and size+len(self.frames[0][0])<=4000000:
                        packet,_=self.frames.popleft();fresh.append(packet);size+=len(packet)
                if not fresh:
                    if time.monotonic()-last_capture>3:
                        report('Kein Spielbild: Spielfenster sichtbar lassen' if not capture_error else 'Spielbild momentan nicht lesbar')
                        self.stop_event.wait(.2)
                    continue
                try:
                    if not self.connection:
                        self.connection=(http.client.HTTPSConnection(base.hostname,base.port,timeout=4,context=tls_context())
                                         if base.scheme=='https' else http.client.HTTPConnection(base.hostname,base.port,timeout=4))
                    self.connection.request('POST',endpoint,body=b''.join(fresh),headers={
                        'Authorization':'Bearer '+self.access['token'],'Content-Type':'application/x-soullink-frames'})
                    response=self.connection.getresponse();raw=response.read(4096)
                    if response.status!=200:
                        self._disconnect()
                        report('Website erneut verbinden' if response.status in (401,403) else 'Website-Update erforderlich' if response.status==404 else 'Verbindung wird wiederhergestellt')
                        self.stop_event.wait(2);continue
                    result=json.loads(raw)
                    if result.get('accepted')!=len(fresh) or result.get('player')!=self.access['player']:
                        raise ValueError('Missing delivery confirmation')
                    report('Live · '+(str(captured)+' FPS Ziel' if captured else 'FPS wie App')+' · Empfang bestätigt',True)
                except (OSError,ValueError,http.client.HTTPException):
                    self._disconnect();report('Verbindung wird wiederhergestellt');self.stop_event.wait(.5)
        finally:
            self.stop_event.set();collector.join(timeout=2);receiver.stop();self._disconnect()
            if timer:timer.timeEndPeriod(1)
            self.frame.unlink(missing_ok=True);status_path.unlink(missing_ok=True)
