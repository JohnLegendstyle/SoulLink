"""Browser-confirmed pairing and a latest-only private game preview."""
from pathlib import Path
import json
import threading
import time
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
    def start(self):
        self.thread=threading.Thread(target=self._run,daemon=True);self.thread.start()
    def stop(self):
        self.stop_event.set()
        self.frame.with_name(self.frame.name+'.enabled').unlink(missing_ok=True)
    def _run(self):
        endpoint=trusted_base(self.access['baseUrl'])+'/api/frame?'+urlencode({'id':self.access['roomId']})
        headers={'Authorization':'Bearer '+self.access['token'],'Content-Type':'image/jpeg'}
        last=None;published=False;status=''
        def report(message):
            nonlocal status
            if message!=status: status=message;self.on_status(message)
        def remove():
            try:
                with urlopen(Request(endpoint,method='DELETE',headers=headers),timeout=3,context=tls_context()): pass
            except Exception: pass
        try:
            while not self.stop_event.wait(.3):
                try:
                    if not self.frame.with_name(self.frame.name+'.enabled').exists():
                        if published: remove();published=False
                        report('Bildvorschau ausgeschaltet');continue
                    stat=self.frame.stat()
                    if time.time()-stat.st_mtime>3:
                        report('Bildvorschau pausiert');continue
                    if stat.st_mtime_ns==last or stat.st_size>300000: continue
                    data=self.frame.read_bytes()
                    if not data.startswith(b'\xff\xd8') or not data.endswith(b'\xff\xd9'): continue
                    with urlopen(Request(endpoint,method='PUT',headers=headers,data=data),timeout=3,context=tls_context()) as response:
                        if response.status!=200: continue
                    last=stat.st_mtime_ns;published=True;report('Private Bildvorschau aktiv · bis 4 Bilder/s · ohne Ton')
                except FileNotFoundError: pass
                except Exception:
                    report('Bildvorschau wartet auf Verbindung');self.stop_event.wait(2)
        finally:
            if published: remove()
            self.frame.unlink(missing_ok=True)
