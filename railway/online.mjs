import {randomUUID} from 'node:crypto';

// Short-lived pairing grants. All video endpoints are permanently retired.
export function onlineRoutes({authorize,send,body,hash,key}) {
  const devices=new Map(), rates=new Map();
  const expire=()=>{
    const now=Date.now();
    for(const [id,d] of devices) if(d.expires<now) devices.delete(id);
    for(const [id,r] of rates) if(now-r.at>60000) rates.delete(id);
  };
  const timer=setInterval(expire,5000);timer.unref();
  return async(req,res,url)=>{
    if(['/api/live','/api/live/batch','/api/frame'].includes(url.pathname)){
      res.setHeader('Connection','close');
      send(res,410,{error:'Bildübertragung entfernt. Bitte in alten Apps Übertragung stoppen. Teams und Spielstände bleiben verbunden.',videoDisabled:true});
      return true;
    }
    if(!['/api/pair','/api/pair/approve'].includes(url.pathname)) return false;
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
    send(res,405,{error:'Methode nicht erlaubt.'});return true;
  };
}
