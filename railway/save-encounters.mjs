// Read-only HGSS report fields. Same block ordering and checks as save_reader.py.
import {validSave} from './cloud.mjs';
const order=[[0,1,2,3],[0,1,3,2],[0,2,1,3],[0,3,1,2],[0,2,3,1],[0,3,2,1],[1,0,2,3],[1,0,3,2],[2,0,1,3],[3,0,1,2],[2,0,3,1],[3,0,2,1],[1,2,0,3],[1,3,0,2],[2,1,0,3],[3,1,0,2],[2,3,0,1],[3,2,0,1],[1,2,3,0],[1,3,2,0],[2,1,3,0],[3,1,2,0],[2,3,1,0],[3,2,1,0]];
export function crc16(bytes){let crc=65535;for(const b of bytes){crc^=b<<8;for(let i=0;i<8;i++)crc=((crc<<1)^((crc&32768)?0x1021:0))&65535;}return crc;}
function active(bytes,start,length){
  const good=[0,0x40000].filter(p=>crc16(bytes.subarray(start+p,start+p+length-16))===bytes.readUInt16LE(start+p+length-2));
  if(!good.length)throw Error('Invalid save block');if(good.length===1)return good[0]+start;
  const x=start+length-20,a=bytes.readUInt32LE(x),b=bytes.readUInt32LE(x+0x40000);
  if(a===0xffffffff&&b!==0xfffffffe)return start+0x40000;
  if(b===0xffffffff&&a!==0xfffffffe)return start;
  return start+(a>b||a===b&&bytes.readUInt32LE(x+4)>=bytes.readUInt32LE(x+0x40004)?0:0x40000);
}
export function pokemonReport(raw){
  const d=Buffer.from(raw.subarray(0,136));if(d.length!==136)return null;
  const pid=d.readUInt32LE(0),checksum=d.readUInt16LE(6);let seed=checksum;
  for(let i=8;i<136;i+=2){seed=(Math.imul(0x41c64e6d,seed)+0x6073)>>>0;d.writeUInt16LE(d.readUInt16LE(i)^(seed>>>16),i);}
  const blocks=Buffer.from(d.subarray(8));order[((pid>>>13)&31)%24].forEach((slot,i)=>blocks.copy(d,8+i*32,slot*32,slot*32+32));
  let sum=0;for(let i=8;i<136;i+=2)sum+=d.readUInt16LE(i);
  const species=d.readUInt16LE(8);if((sum&65535)!==checksum||species<1||species>493)return null;
  return {uid:pid.toString(16).padStart(8,'0')+'-'+d.readUInt32LE(12).toString(16).padStart(8,'0'),
    metLocation:d.readUInt16LE(0x46)||d.readUInt16LE(0x80)||null,
    originGame:d[0x5f],eggLocation:d.readUInt16LE(0x44)||d.readUInt16LE(0x7e),isEgg:!!(d.readUInt32LE(0x38)&(1<<30))};
}
export function reports(bytes,role){
  bytes=Buffer.from(bytes);if(!validSave(bytes,role))throw Error('Invalid save or player');
  const g=active(bytes,0,0xf628),s=active(bytes,0xf700,0x12310),out=new Map();
  const add=(offset)=>{const p=pokemonReport(bytes.subarray(offset,offset+136));if(p)out.set(p.uid,p);};
  for(let b=0;b<18;b++)for(let i=0;i<30;i++)add(s+b*0x1000+i*136);
  for(let i=0;i<Math.min(bytes[g+0x94],6);i++)add(g+0x98+i*236);
  return out;
}
export function enrichMember(member,found){
  let changed=0;
  for(const mon of [...(member.seen||[]),...(member.party||[])]){
    const p=found.get(mon.uid);
    // Only fill missing report data on already-known identities. Never change
    // team order, caught order, HP, names, KO rules or manual route decisions.
    if(p?.metLocation&&!mon.metLocation){for(const k of ['metLocation','originGame','eggLocation','isEgg'])mon[k]=p[k];changed++;}
  }
  return changed;
}
export function backfillEncounters(db){
  let filled=0;
  for(const room of db.prepare('SELECT id,state FROM rooms').all()){
    const state=JSON.parse(room.state);let changed=0;
    for(const role of ['John','Eddie']){
      if(!state[role]?.seen?.some(m=>!m.metLocation))continue;
      const found=new Map();
      for(const v of db.prepare('SELECT data FROM cloud_versions WHERE room=? AND role=? ORDER BY revision DESC').all(room.id,role)){
        try{for(const [uid,p] of reports(v.data,role))if(!found.has(uid))found.set(uid,p);}catch{/* Ignore damaged/foreign snapshots without modifying them. */}
      }
      changed+=enrichMember(state[role],found);
    }
    if(changed){db.prepare('UPDATE rooms SET state=?,revision=revision+1 WHERE id=?').run(JSON.stringify(state),room.id);filled+=changed;}
  }
  return filled;
}
