import {randomBytes,scryptSync,timingSafeEqual,createHash,createCipheriv,createDecipheriv} from 'node:crypto';
import {readFileSync} from 'node:fs';

export function siteAuth(db,send,body){
  const encoded=process.env.SOULLINK_PASSWORD_HASH||'';
  const sessions=new Map(),attempts=new Map();
  db.exec('CREATE TABLE IF NOT EXISTS site_settings(name TEXT PRIMARY KEY,value TEXT NOT NULL)');
  const cipherKey=createHash('sha256').update(encoded+'|SoulLink private account room').digest();
  function saveRoom(room){
    const iv=randomBytes(12),cipher=createCipheriv('aes-256-gcm',cipherKey,iv);
    const content=Buffer.concat([cipher.update(JSON.stringify(room),'utf8'),cipher.final()]);
    const sealed=Buffer.concat([iv,cipher.getAuthTag(),content]).toString('base64');
    db.prepare('INSERT INTO site_settings(name,value) VALUES(?,?) ON CONFLICT(name) DO UPDATE SET value=excluded.value').run('active_room',sealed);
  }
  function currentRoom(user){
    const row=db.prepare('SELECT value FROM site_settings WHERE name=?').get('active_room');
    if(!row)return null;
    const bytes=Buffer.from(row.value,'base64'),decipher=createDecipheriv('aes-256-gcm',cipherKey,bytes.subarray(0,12));
    decipher.setAuthTag(bytes.subarray(12,28));
    const room=JSON.parse(Buffer.concat([decipher.update(bytes.subarray(28)),decipher.final()]).toString());
    return {id:room.id,readToken:room.readToken,[user]:room[user]};
  }
  function session(req){
    const token=req.headers.cookie?.split(';').map(s=>s.trim()).find(s=>s.startsWith('soullink_session='))?.split('=')[1];
    const value=token&&sessions.get(token);
    return value&&value.expires>Date.now()?value.user:null;
  }
  setInterval(()=>{for(const [id,s] of sessions)if(s.expires<Date.now())sessions.delete(id);for(const [id,a] of attempts)if(Date.now()-a.at>900000)attempts.delete(id);},60000).unref();
  async function guard(req,res,url){
    req.soulUser=session(req);
    if(url.pathname==='/health')return false;
    if(!encoded){send(res,503,{error:'Website-Zugang wird eingerichtet.'});return true;}
    if(url.pathname==='/api/login'&&req.method==='POST'){
      const origin=req.headers.origin;
      if(origin&&new URL(origin).host!==req.headers.host){send(res,403,{error:'Ungültige Herkunft.'});return true;}
      const ip=req.headers['x-forwarded-for']||req.socket.remoteAddress;
      if(attempts.size>=10000&&!attempts.has(ip)){send(res,429,{error:'Bitte später erneut versuchen.'});return true;}
      const limit=attempts.get(ip)||{n:0,at:Date.now()};attempts.set(ip,limit);
      if(++limit.n>20){send(res,429,{error:'Zu viele Versuche. Bitte 15 Minuten warten.'});return true;}
      const b=await body(req),user=String(b.username||'').trim().toLowerCase();
      const [salt,expected]=encoded.split(':');
      const input=typeof b.password==='string'&&b.password.length<=128?b.password:'';
      const actual=scryptSync(input,salt,32),reference=Buffer.from(expected||'','hex');
      const correct=reference.length===actual.length&&timingSafeEqual(reference,actual);
      if(!correct||!['john','eddie'].includes(user)){send(res,401,{error:'Anmeldename oder Passwort ist falsch.'});return true;}
      if(sessions.size>2000){send(res,503,{error:'Bitte später versuchen.'});return true;}
      const token=randomBytes(32).toString('hex');sessions.set(token,{user:user==='john'?'John':'Eddie',expires:Date.now()+86400000});
      attempts.delete(ip);
      const secure=process.env.SOULLINK_LOCAL_TEST==='1'?'':'; Secure';
      res.setHeader('Set-Cookie',`soullink_session=${token}; HttpOnly; SameSite=Lax; Path=/; Max-Age=86400${secure}`);
      send(res,200,{ok:true});return true;
    }
    if(url.pathname==='/api/logout'&&req.method==='POST'){
      const token=req.headers.cookie?.match(/(?:^|;\s*)soullink_session=([a-f0-9]+)/)?.[1];
      if(token)sessions.delete(token);
      res.setHeader('Set-Cookie','soullink_session=; HttpOnly; SameSite=Lax; Secure; Path=/; Max-Age=0');send(res,200,{ok:true});return true;
    }
    // Apps use scoped bearer grants, not the website password or browser cookies.
    if(['/api/sync','/api/frame','/api/pair','/api/cloud-save','/api/cloud-save/lease'].includes(url.pathname))return false;
    if(!req.soulUser){
      if(url.pathname.startsWith('/api/'))send(res,401,{error:'Bitte auf der Website anmelden.'});
      else {res.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store','Referrer-Policy':'no-referrer','X-Content-Type-Options':'nosniff','Content-Security-Policy':"default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'; form-action 'self'; base-uri 'none'"});res.end(readFileSync(new URL('./login.html',import.meta.url)));}
      return true;
    }
    if(url.pathname==='/api/account'&&req.method==='GET'){send(res,200,{user:req.soulUser,access:currentRoom(req.soulUser)});return true;}
    return false;
  }
  return {guard,saveRoom,currentRoom};
}
