import {createHash} from 'node:crypto';

const hex=s=>typeof s==='string'&&/^[a-f0-9]{64}$/.test(s);
const digest=b=>createHash('sha256').update(b).digest('hex');
function crc16(bytes){let crc=65535;for(const b of bytes){crc^=b<<8;for(let i=0;i<8;i++)crc=((crc<<1)^((crc&32768)?0x1021:0))&65535;}return crc;}
export function validSave(bytes,role){
  if(bytes.length!==524288)return false;
  let general=false,storage=false;
  const trainer=role==='John'?'Optimus':'Bee';
  for(const base of [0,0x40000]){
    if(crc16(bytes.subarray(base,base+0xf628-16))===bytes.readUInt16LE(base+0xf628-2)){
      let name='';for(let i=0;i<8;i++){const c=bytes.readUInt16LE(base+0x64+2*i);if(c===0||c===65535)break;name+=c>=0x12b&&c<=0x144?String.fromCharCode(65+c-0x12b):c>=0x145&&c<=0x15e?String.fromCharCode(97+c-0x145):'?';}
      if(name!==trainer)return false;
      general=true;
    }
    const start=base+0xf700;
    if(crc16(bytes.subarray(start,start+0x12310-16))===bytes.readUInt16LE(start+0x12310-2))storage=true;
  }
  return general&&storage;
}

export function cloudRoutes({db,authorize,send,body}){
  db.exec(`CREATE TABLE IF NOT EXISTS cloud_saves(
    room TEXT NOT NULL,role TEXT NOT NULL,rom_hash TEXT NOT NULL,revision INTEGER NOT NULL DEFAULT 0,
    sha TEXT NOT NULL DEFAULT '',updated_at INTEGER NOT NULL DEFAULT 0,
    lease_hash TEXT NOT NULL DEFAULT '',lease_until INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY(room,role));
    CREATE TABLE IF NOT EXISTS cloud_versions(
    room TEXT NOT NULL,role TEXT NOT NULL,revision INTEGER NOT NULL,sha TEXT NOT NULL,
    created_at INTEGER NOT NULL,data BLOB NOT NULL,PRIMARY KEY(room,role,revision));`);
  const get=(id,role)=>db.prepare('SELECT * FROM cloud_saves WHERE room=? AND role=?').get(id,role);
  const info=row=>row?{revision:row.revision,sha256:row.sha,romHash:row.rom_hash,updatedAt:row.updated_at}:null;
  return async(req,res,url)=>{
    if(!['/api/cloud-save','/api/cloud-save/lease'].includes(url.pathname))return false;
    const id=url.searchParams.get('id'),a=authorize(req,id);
    if(!a||a.role==='read'){send(res,403,{error:'Nur dein eigener Spielerzugang darf Spielstände abrufen.'});return true;}
    const role=a.role;
    if(req.method==='GET'&&url.pathname==='/api/cloud-save'){
      const row=get(id,role),revision=url.searchParams.get('revision');
      if(revision!==null){
        if(!/^[1-9][0-9]{0,9}$/.test(revision)){send(res,400,{error:'Ungültige Version.'});return true;}
        const v=db.prepare('SELECT * FROM cloud_versions WHERE room=? AND role=? AND revision=?').get(id,role,Number(revision));
        if(!v){send(res,404,{error:'Sicherung nicht gefunden.'});return true;}
        send(res,200,{revision:v.revision,sha256:v.sha,data:Buffer.from(v.data).toString('base64')});return true;
      }
      const versions=db.prepare('SELECT revision,sha AS sha256,created_at AS updatedAt FROM cloud_versions WHERE room=? AND role=? ORDER BY revision DESC').all(id,role);
      send(res,200,{current:info(row),versions});return true;
    }
    if(!['POST','PUT'].includes(req.method)){send(res,405,{error:'Methode nicht erlaubt.'});return true;}
    const b=await body(req,800000);
    if(!hex(b.lease)||!hex(b.romHash)){send(res,400,{error:'Ungültige Cloud-Sitzung.'});return true;}
    const leaseHash=digest(b.lease);
    // No await inside this transaction: lease, ROM identity and revision form one atomic check.
    db.exec('BEGIN IMMEDIATE');
    try{
      let row=get(id,role),now=Date.now();
      if(row&&row.rom_hash!==b.romHash){db.exec('ROLLBACK');send(res,409,{code:'ROM_MISMATCH',error:'Diese Website-Runde gehört zu einer anderen randomisierten ROM. Bitte dieselbe Runde öffnen.'});return true;}
      if(url.pathname==='/api/cloud-save/lease'&&req.method==='POST'){
        if(b.release===true){
          if(row?.lease_hash===leaseHash)db.prepare('UPDATE cloud_saves SET lease_hash=?,lease_until=0 WHERE room=? AND role=?').run('',id,role);
          db.exec('COMMIT');send(res,200,{ok:true});return true;
        }
        if(row&&row.lease_until>now&&row.lease_hash!==leaseHash){db.exec('ROLLBACK');send(res,423,{code:'BUSY',error:'Dieser Spieler ist auf einem anderen Gerät aktiv. Dort speichern und das Spielfenster schließen. Nach einem Absturz bis zu 90 Sekunden warten.'});return true;}
        if(!row)db.prepare('INSERT INTO cloud_saves(room,role,rom_hash) VALUES(?,?,?)').run(id,role,b.romHash);
        db.prepare('UPDATE cloud_saves SET lease_hash=?,lease_until=? WHERE room=? AND role=?').run(leaseHash,now+90000,id,role);
        row=get(id,role);db.exec('COMMIT');send(res,200,{current:info(row)});return true;
      }
      if(url.pathname!=='/api/cloud-save'||req.method!=='PUT'){db.exec('ROLLBACK');send(res,405,{error:'Methode nicht erlaubt.'});return true;}
      if(!row||row.lease_hash!==leaseHash||row.lease_until<=now){db.exec('ROLLBACK');send(res,423,{code:'LEASE_LOST',error:'Cloud-Sitzung abgelaufen. Dein lokaler Stand bleibt erhalten. Spiel schließen und neu abgleichen.'});return true;}
      if(!Number.isSafeInteger(b.baseRevision)||b.baseRevision<0||typeof b.data!=='string'||b.data.length!==699052||!/^[A-Za-z0-9+/]+={0,2}$/.test(b.data)){
        db.exec('ROLLBACK');send(res,400,{error:'Ungültiger Spielstand.'});return true;
      }
      const data=Buffer.from(b.data,'base64'),sha=digest(data);
      if(!validSave(data,role)){db.exec('ROLLBACK');send(res,400,{error:'Spielstand unvollständig, beschädigt oder falscher Trainer.'});return true;}
      // Retrying a request whose response was lost is safe and does not create another version.
      if(row.sha===sha){db.exec('COMMIT');send(res,200,{current:info(row)});return true;}
      if(row.revision!==b.baseRevision){db.exec('ROLLBACK');send(res,409,{code:'CONFLICT',error:'Es gibt inzwischen einen anderen Cloud-Stand. Keine Datei wurde überschrieben.'});return true;}
      const revision=row.revision+1;
      db.prepare('INSERT INTO cloud_versions(room,role,revision,sha,created_at,data) VALUES(?,?,?,?,?,?)').run(id,role,revision,sha,now,data);
      db.prepare('UPDATE cloud_saves SET revision=?,sha=?,updated_at=? WHERE room=? AND role=?').run(revision,sha,now,id,role);
      db.prepare('DELETE FROM cloud_versions WHERE room=? AND role=? AND revision<=?').run(id,role,revision-10);
      row=get(id,role);db.exec('COMMIT');send(res,200,{current:info(row)});return true;
    }catch(e){try{db.exec('ROLLBACK');}catch{}throw e;}
  };
}
