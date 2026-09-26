import http from 'node:http';
import {DatabaseSync} from 'node:sqlite';
import {createHash,randomUUID,randomBytes} from 'node:crypto';
import {mkdirSync,readFileSync,existsSync} from 'node:fs';
import path from 'node:path';
import {onlineRoutes} from './online.mjs';
import {siteAuth} from './auth.mjs';
import {cloudRoutes} from './cloud.mjs';
const dir=process.env.DATA_DIR||'./data';mkdirSync(dir,{recursive:true});
const db=new DatabaseSync(path.join(dir,'soullink.sqlite'));db.exec('PRAGMA journal_mode=WAL; PRAGMA busy_timeout=5000; CREATE TABLE IF NOT EXISTS rooms(id TEXT PRIMARY KEY, read_hash TEXT NOT NULL,john_hash TEXT NOT NULL,eddie_hash TEXT NOT NULL,state TEXT NOT NULL,revision INTEGER NOT NULL DEFAULT 0,created_at INTEGER NOT NULL);');
const hash=s=>createHash('sha256').update(s).digest('hex'),key=()=>randomBytes(32).toString('hex');
const player=()=>({party:[],seen:[],dead:[],lastSeen:0,sessionId:'',sequence:-1});
const initial=()=>({John:player(),Eddie:player(),names:{}});
function authorize(req,id){if(typeof id!=='string'||!/^[a-f0-9-]{36}$/.test(id))return null;const token=req.headers.authorization?.replace(/^Bearer /,'');if(!token||!/^[a-f0-9]{64}$/.test(token))return null;const row=db.prepare('SELECT * FROM rooms WHERE id=?').get(id);if(!row)return null;const h=hash(token);const role=h===row.john_hash?'John':h===row.eddie_hash?'Eddie':h===row.read_hash?'read':null;return role?{row,role,state:JSON.parse(row.state)}:null;}
function blocked(s,p){const o=p==='John'?'Eddie':'John';return s[p].seen.filter((m,i)=>s[p].dead.includes(m.uid)||(s[o].seen[i]&&s[o].dead.includes(s[o].seen[i].uid))).map(m=>m.uid);}
function clean(v,box=false){if(!v||typeof v.uid!=='string'||!v.uid.length||v.uid.length>100||!Number.isInteger(v.species)||v.species<1||v.species>493)throw Error('Ungültige Pokémon-Daten');if(box&&v.level==null)return {uid:v.uid,species:v.species,nickname:String(v.nickname||'').slice(0,30),level:null,hp:null,maxHp:null};if(!Number.isInteger(v.level)||v.level<1||v.level>100||!Number.isInteger(v.hp)||!Number.isInteger(v.maxHp)||v.maxHp<1||v.maxHp>999||v.hp<0||v.hp>v.maxHp)throw Error('Ungültige KP/Level');return{uid:v.uid,species:v.species,nickname:String(v.nickname||'').slice(0,30),level:v.level,hp:v.hp,maxHp:v.maxHp};}
const headers={'Content-Type':'application/json','Cache-Control':'no-store','Referrer-Policy':'no-referrer','X-Content-Type-Options':'nosniff'};
function send(res,status,data){res.writeHead(status,headers);res.end(JSON.stringify(data));}
async function body(req,limit=300000){let s='';for await(const b of req){s+=b;if(s.length>limit)throw Error('Anfrage zu groß');}return s?JSON.parse(s):{};}
const rate=new Map();
const online=onlineRoutes({authorize,send,body,hash,key});
const auth=siteAuth(db,send,body);
const cloud=cloudRoutes({db,authorize,send,body});
const server=http.createServer(async(req,res)=>{try{const url=new URL(req.url,'http://localhost');
if(await auth.guard(req,res,url))return;
if(await cloud(req,res,url))return;
if(await online(req,res,url))return;
if(url.pathname==='/health')return send(res,200,{ok:true});
if(url.pathname==='/api/room'&&req.method==='POST'){
const ip=req.headers['x-forwarded-for']||req.socket.remoteAddress;const old=rate.get(ip)||{at:Date.now(),n:0};if(Date.now()-old.at>3600000){old.at=Date.now();old.n=0;}if(old.n++>=20)return send(res,429,{error:'Zu viele neue Runden. Bitte später erneut versuchen.'});rate.set(ip,old);if(rate.size>10000)rate.clear();
const id=randomUUID(),readToken=key(),John=key(),Eddie=key();db.prepare('INSERT INTO rooms(id,read_hash,john_hash,eddie_hash,state,created_at) VALUES(?,?,?,?,?,?)').run(id,hash(readToken),hash(John),hash(Eddie),JSON.stringify(initial()),Date.now());
auth.saveRoom({id,readToken,John,Eddie});return send(res,200,auth.currentRoom(req.soulUser));}
if(url.pathname==='/api/room'&&req.method==='GET'){const a=authorize(req,url.searchParams.get('id'));return a?send(res,200,{state:a.state,revision:a.row.revision}):send(res,401,{error:'Der Zugang ist ungültig.'});}
if(url.pathname==='/api/room'&&req.method==='PATCH'){const b=await body(req);const a=authorize(req,b.id);if(!a)return send(res,401,{error:'Zugang ungültig.'});if(!Number.isInteger(b.pair)||b.pair<0||b.pair>9999||typeof b.name!=='string'||b.name.trim().length>32)return send(res,400,{error:'Ungültiger Paarname'});a.state.names[b.pair]=b.name.trim();db.prepare('UPDATE rooms SET state=?,revision=revision+1 WHERE id=?').run(JSON.stringify(a.state),b.id);return send(res,200,{ok:true});}
if(url.pathname==='/api/sync'&&req.method==='POST'){const b=await body(req);const a=authorize(req,b.roomId);if(!a||a.role==='read')return send(res,401,{error:'Ungültiger Spielerzugang'});if(b.heartbeat===true){const who=a.role,other=who==='John'?'Eddie':'John';a.state[who].lastSeen=Date.now();db.prepare('UPDATE rooms SET state=?,revision=revision+1 WHERE id=?').run(JSON.stringify(a.state),b.roomId);return send(res,200,{ok:true,blocked:blocked(a.state,who),partnerOnline:Date.now()-a.state[other].lastSeen<10000});}if(typeof b.sessionId!=='string'||b.sessionId.length>100||!Number.isSafeInteger(b.sequence)||b.sequence<0||!Array.isArray(b.party)||b.party.length>6||!Array.isArray(b.fainted)||b.fainted.length>1000||b.fainted.some(v=>typeof v!=='string'||v.length>100)||b.owned!==undefined&&(!Array.isArray(b.owned)||b.owned.length>546))return send(res,400,{error:'Ungültige Synchronisierung'});const party=b.party.map(m=>clean(m));if(new Set(party.map(m=>m.uid)).size!==party.length)return send(res,400,{error:'Doppelte Team-ID'});const who=a.role,other=who==='John'?'Eddie':'John',p=a.state[who];if(p.sessionId===b.sessionId&&p.sequence>=b.sequence)return send(res,200,{ok:true,blocked:blocked(a.state,who),partnerOnline:Date.now()-a.state[other].lastSeen<10000});p.party=party;p.lastSeen=Date.now();p.sessionId=b.sessionId;p.sequence=b.sequence;
for(const m of [...(b.owned||[]).map(m=>clean(m,true)),...party]){const ix=p.seen.findIndex(x=>x.uid===m.uid);if(ix<0){if(p.seen.length>=1000)return send(res,400,{error:'Runde ist voll'});p.seen.push(m);}else p.seen[ix]=m;}
for(const uid of b.fainted)if(p.seen.some(m=>m.uid===uid)&&!p.dead.includes(uid))p.dead.push(uid);
db.prepare('UPDATE rooms SET state=?,revision=revision+1 WHERE id=?').run(JSON.stringify(a.state),b.roomId);return send(res,200,{ok:true,blocked:blocked(a.state,who),partnerOnline:Date.now()-a.state[other].lastSeen<10000});}
if(url.pathname.startsWith('/api/'))return send(res,404,{error:'Nicht gefunden'});
if(req.method!=='GET'&&req.method!=='HEAD')return send(res,405,{error:'Methode nicht erlaubt'});
let pathname;try{pathname=decodeURIComponent(url.pathname)}catch{return send(res,400,{error:'Ungültiger Pfad'})}const root=path.resolve(process.env.PUBLIC_DIR||'./public');let file=path.resolve(root,'.'+pathname);if(file!==root&&!file.startsWith(root+path.sep))return send(res,404,{error:'Nicht gefunden'});if(pathname==='/'||!path.extname(pathname))file=path.join(root,'index.html');if(!existsSync(file))return send(res,404,{error:'Nicht gefunden'});const mime={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.svg':'image/svg+xml','.png':'image/png'}[path.extname(file)]||'application/octet-stream';res.writeHead(200,{'Content-Type':mime,'Referrer-Policy':'no-referrer','X-Content-Type-Options':'nosniff','Cache-Control':file.endsWith('.html')?'no-cache':'public,max-age=3600'});res.end(req.method==='HEAD'?undefined:readFileSync(file));
}catch(e){console.error('Request rejected:',e instanceof SyntaxError?'invalid JSON':'invalid request');send(res,400,{error:'Die Anfrage konnte nicht verarbeitet werden.'});}});
server.listen(Number(process.env.PORT||3000),'0.0.0.0',()=>console.log('SoulLink ready '+server.address().port));
