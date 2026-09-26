"""Browser-confirmed pairing and a latest-only private game preview."""
from pathlib import Path
import json
import threading
import time
import http.client
import os
import socket
import struct
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
        on_status('Bitte im Browser einmal Optimus oder Bee bestätigen. Danach verbindet sich die App automatisch.')
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
        base=urlsplit(trusted_base(self.access['baseUrl']))
        endpoint='/api/live?'+urlencode({'id':self.access['roomId']})
        last=None;status='';opened=0;last_send=0
        timer=None
        if os.name=='nt':
            import ctypes
            timer=ctypes.windll.winmm;timer.timeBeginPeriod(1)
        def report(message):
            nonlocal status
            if message!=status: status=message;self.on_status(message)
        def send(packet):
            self.connection.send(('%x\r\n'%len(packet)).encode()+packet+b'\r\n')
        try:
            while not self.stop_event.wait(.001):
                try:
                    if not self.frame.with_name(self.frame.name+'.enabled').exists():
                        self._disconnect();last=None
                        report('Bildübertragung ausgeschaltet');self.stop_event.wait(.1);continue
                    if self.connection and time.monotonic()-opened>50:self._disconnect();last=None
                    if not self.connection:
                        if base.scheme=='https': connection=http.client.HTTPSConnection(base.hostname,base.port,timeout=3,context=tls_context())
                        else: connection=http.client.HTTPConnection(base.hostname,base.port,timeout=3)
                        self.connection=connection
                        connection.putrequest('PUT',endpoint)
                        connection.putheader('Authorization','Bearer '+self.access['token'])
                        connection.putheader('Content-Type','application/x-soullink-frames')
                        connection.putheader('Transfer-Encoding','chunked');connection.endheaders()
                        response=connection.getresponse()
                        if response.status!=200:raise OSError('Stream rejected')
                        opened=time.monotonic();last_send=opened;last=None
                    if time.monotonic()-last_send>1:
                        send(struct.pack('!IHH',0,0,2));last_send=time.monotonic()
                    stat=self.frame.stat()
                    if time.time()-stat.st_mtime>3:
                        report('Bildübertragung pausiert');self.stop_event.wait(.05);continue
                    if stat.st_mtime_ns==last or stat.st_size>300008: continue
                    packet,fps=self.packet(self.frame.read_bytes());send(packet)
                    last=stat.st_mtime_ns;last_send=time.monotonic()
                    report('Bildübertragung · '+(str(fps)+' FPS als Ziel' if fps else 'FPS wie App: unbegrenzt')+' · ohne Ton')
                except FileNotFoundError: pass
                except Exception:
                    self._disconnect();last=None
                    report('Bildübertragung wartet auf Verbindung');self.stop_event.wait(2)
        finally:
            self._disconnect()
            if timer:timer.timeEndPeriod(1)
            self.frame.unlink(missing_ok=True)
