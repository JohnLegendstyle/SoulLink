import {placeIds} from '../lib/encounters.mjs';

export function encounterRoutes({authorize,send,body,db}){
  return async(req,res,url)=>{
    if(url.pathname!=='/api/encounters')return false;
    if(req.method!=='PATCH'){send(res,405,{error:'PATCH erforderlich.'});return true;}
    const b=await body(req,4096),a=authorize(req,b.id);
    if(!a||a.role==='read'||a.role!==req.soulUser){send(res,403,{error:'Nur der eigene Spieler darf Fangorte ändern.'});return true;}
    if(!placeIds.has(b.location)||!['caught','missed','open','auto'].includes(b.status)){
      send(res,400,{error:'Ungültiger Fangort oder Status.'});return true;
    }
    const member=a.state[a.role];member.encounters??={};
    if(b.status==='auto')delete member.encounters[b.location];
    else member.encounters[b.location]={status:b.status,updatedAt:Date.now()};
    db.prepare('UPDATE rooms SET state=?,revision=revision+1 WHERE id=?').run(JSON.stringify(a.state),b.id);
    send(res,200,{ok:true,player:a.role,encounters:member.encounters});return true;
  };
}
