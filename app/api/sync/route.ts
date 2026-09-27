import {authorize,blocked,cleanMon,cleanOwned,cleanPosition,db,response} from '@/lib/soul';
import {placeSeen} from '@/lib/encounters.mjs';

export async function POST(req:Request){
  try{
    if(Number(req.headers.get('content-length')||0)>50000)return response({error:'Zu groß'},413);
    const text=await req.text();if(text.length>50000)return response({error:'Zu groß'},413);
    const b=JSON.parse(text);
    if(typeof b.roomId!=='string')return response({error:'Ungültige Synchronisierung'},400);
    for(let i=0;i<8;i++){
      const a=await authorize(req,b.roomId);
      if(!a||a.role==='read')return response({error:'Ungültiger Spielerzugang'},401);
      const who=a.role as 'John'|'Eddie',other=who==='John'?'Eddie':'John',p=a.state[who];
      if(b.heartbeat===true){
        p.lastSeen=Date.now();if(b.position!==undefined)p.position=cleanPosition(b.position);
      }else{
        if(typeof b.sessionId!=='string'||b.sessionId.length>100||!Number.isSafeInteger(b.sequence)||b.sequence<0||!Array.isArray(b.party)||b.party.length>6||!Array.isArray(b.fainted)||b.fainted.length>1000||b.fainted.some((v:unknown)=>typeof v!=='string'||v.length>100))return response({error:'Ungültige Synchronisierung'},400);
        const party=b.party.map(cleanMon);if(new Set(party.map((mon:any)=>mon.uid)).size!==party.length)return response({error:'Doppelte Team-ID'},400);
        if(p.sessionId===b.sessionId&&p.sequence>=b.sequence)return response({ok:true,blocked:blocked(a.state,who),partnerOnline:Date.now()-a.state[other].lastSeen<10000});
        p.party=party;p.lastSeen=Date.now();p.sessionId=b.sessionId;p.sequence=b.sequence;
        p.teamSource=b.teamSource==='live'?'live':'save';p.teamCapturedAt=Number.isSafeInteger(b.teamCapturedAt)&&b.teamCapturedAt>0?Math.min(b.teamCapturedAt,Date.now()):0;
        if(b.position!==undefined)p.position=cleanPosition(b.position);
        if(b.owned!==undefined&&(!Array.isArray(b.owned)||b.owned.length>546))return response({error:'Ungültige Boxdaten'},400);
        for(const mon of [...(b.owned||[]).map(cleanOwned),...party]){if(!p.seen.some(item=>item?.uid===mon.uid)&&p.seen.length>=1000)return response({error:'Runde ist voll'},400);placeSeen(a.state,who,mon);}
        for(const uid of b.fainted)if(p.seen.some(mon=>mon?.uid===uid)&&!p.dead.includes(uid))p.dead.push(uid);
      }
      const result=await db().prepare('UPDATE rooms SET state=?,revision=revision+1 WHERE id=? AND revision=?').bind(JSON.stringify(a.state),b.roomId,a.row.revision).run();
      if(result.meta.changes)return response({ok:true,blocked:blocked(a.state,who),partnerOnline:Date.now()-a.state[other].lastSeen<10000});
    }
    return response({error:'Bitte erneut synchronisieren'},409);
  }catch(e){console.error(e);return response({error:'Synchronisierung derzeit nicht möglich'},503);}
}
