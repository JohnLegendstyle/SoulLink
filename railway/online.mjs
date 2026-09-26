import {randomUUID} from 'node:crypto';
import {liveRelay} from './live.mjs';

// Short-lived pairing grants and latest-only previews. No recordings on disk.
export function onlineRoutes({authorize,send,body,hash,key}) {
  const devices=new Map(), frames=new Map(), rates=new Map();
  const live=liveRelay({authorize,send,onFrame:(key,jpeg)=>frames.set(key,{jpeg,at:Date.now()})});
  const expire=()=>{
    const now=Date.now();
    for(const [id,d] of devices) if(d.expires<now) devices.delete(id);
    for(const [id,f] of frames) if(now-f.at>6000) frames.delete(id);
    for(const [id,r] of rates) if(now-r.at>60000) rates.delete(id);
  };
  const timer=setInterval(expire,5000);timer.unref();
  return async(req,res,url)=>{
    if(await live.handle(req,res,url))return true;
    if(!['/api/pair','/api/pair/approve','/api/frame'].includes(url.pathname)) return false;
    expire();
    if(url.pathname==='/api/pair'&&req.method==='POST') {
      const ip=req.headers['x-forwarded-for']||req.socket.remoteAddress;
      const r=rates.get(ip)||{at:Date.now(),n:0};rates.set(ip,r);
      if(++r.n>10||devices.size>=500) {send(res,429,{error:'Bitte kurz warten und erneut verbinden.'});return true;}
      const id=randomUUID(),secret=key(),expires=Date.now()+300000;
      devices.set(id,{secretHash:hash(secret),expires,access:null});
      send(res,200,{id,secret,expires});return true;
    }
    if(url.pathname==='/api/pair'&&req.method==='GET') {
      const d=devices.get(url.searchParams.get('id'));
      const token=req.headers.authorization?.replace(/^Bearer /,'');
      if(!d||!token||token.length!==64||hash(token)!==d.secretHash) send(res,401,{error:'Verbindung abgelaufen. Bitte neu starten.'});
      else send(res,200,{status:d.access?'approved':'pending',access:d.access});
      return true;
    }
    if(url.pathname==='/api/pair/approve'&&req.method==='POST') {
      const b=await body(req),a=authorize(req,b.roomId),d=devices.get(b.deviceId);
      if(!a||a.role==='read'||a.role!==req.soulUser||typeof b.readToken!=='string'||hash(b.readToken)!==a.row.read_hash) {send(res,401,{error:'Bitte mit dem passenden Spieler anmelden. Ein Zuschauer-Link reicht nicht.'});return true;}
      if(!d) {send(res,410,{error:'App-Verbindung abgelaufen. Bitte in der App erneut starten.'});return true;}
      if(d.access) {send(res,409,{error:'Dieses Gerät wurde bereits bestätigt.'});return true;}
      d.access={roomId:b.roomId,player:a.role,token:req.headers.authorization.slice(7),readToken:b.readToken};
      send(res,200,{ok:true,player:a.role});return true;
    }
    if(url.pathname==='/api/frame') {
      const id=url.searchParams.get('id'),a=authorize(req,id);
      if(!a) {send(res,401,{error:'Privater Zugang erforderlich.'});return true;}
      if(req.method==='PUT'||req.method==='DELETE') {
        if(a.role==='read') {send(res,403,{error:'Nur der Spieler darf sein Bild übertragen.'});return true;}
        const frameKey=id+':'+a.role;
        if(req.method==='DELETE') {frames.delete(frameKey);live.clear(frameKey);send(res,200,{ok:true});return true;}
        const previous=frames.get(frameKey);
        if(previous&&Date.now()-previous.at<200) {send(res,429,{error:'Maximal fünf Bilder pro Sekunde.'});return true;}
        if(req.headers['content-type']!=='image/jpeg') {send(res,415,{error:'JPEG erforderlich.'});return true;}
        let size=0;const chunks=[];
        for await(const chunk of req) {size+=chunk.length;if(size>300000) throw Error('Bild zu groß');chunks.push(chunk);}
        const jpeg=Buffer.concat(chunks);
        if(jpeg.length<4||jpeg[0]!==255||jpeg[1]!==216||jpeg.at(-2)!==255||jpeg.at(-1)!==217) {send(res,400,{error:'Ungültiges Bild.'});return true;}
        if(!previous&&frames.size>=100) {send(res,503,{error:'Vorschau ausgelastet.'});return true;}
        live.publish(frameKey,jpeg,4);send(res,200,{ok:true});return true;
      }
      if(req.method==='GET') {
        const role=url.searchParams.get('player');
        if(!['John','Eddie'].includes(role)) {send(res,400,{error:'Unbekannter Spieler.'});return true;}
        const f=frames.get(id+':'+role);
        const headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer'};
        if(!f) {res.writeHead(204,headers);res.end();return true;}
        res.writeHead(200,{...headers,'Content-Type':'image/jpeg','X-Frame-Time':String(f.at)});res.end(f.jpeg);return true;
      }
    }
    send(res,405,{error:'Methode nicht erlaubt.'});return true;
  };
}
