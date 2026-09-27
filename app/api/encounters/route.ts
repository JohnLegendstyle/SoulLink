import {authorize,db,response} from '@/lib/soul';
import {placeIds,ensureMissedSlot} from '@/lib/encounters.mjs';
export async function PATCH(req:Request){
  try{
    const text=await req.text();if(text.length>4096)return response({error:'Zu groß'},413);
    const b=JSON.parse(text);
    if(!placeIds.has(b.location)||!['caught','missed','open','auto'].includes(b.status))return response({error:'Ungültige Markierung'},400);
    for(let attempt=0;attempt<8;attempt++){
      const a=await authorize(req,b.id);if(!a||a.role==='read')return response({error:'Spielerzugang erforderlich'},403);
      const player=a.role as 'John'|'Eddie',member=a.state[player];member.encounters??={};
      const updatedAt=Date.now();
      if(b.status==='auto')delete member.encounters[b.location];else member.encounters[b.location]={status:b.status,updatedAt};
      if(b.status==='missed')ensureMissedSlot(a.state,player,b.location,updatedAt);
      const result=await db().prepare('UPDATE rooms SET state=?,revision=revision+1 WHERE id=? AND revision=?').bind(JSON.stringify(a.state),b.id,a.row.revision).run();
      if(result.meta.changes)return response({ok:true,player,encounters:member.encounters});
    }
    return response({error:'Bitte erneut versuchen'},409);
  }catch{return response({error:'Markierung nicht gespeichert'},400);}
}
