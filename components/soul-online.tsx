'use client';
import {useEffect,useState,type ReactNode} from 'react';
import {LiveParty,type LiveMember} from './live-party';
export type SoulAccess={id:string,readToken:string,John?:string,Eddie?:string};
const token=(v:unknown):v is string=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);
function valid(a:any):a is SoulAccess{return !!a&&/^[a-f0-9-]{36}$/.test(a.id)&&token(a.readToken)&&(!a.John||token(a.John))&&(!a.Eddie||token(a.Eddie));}
export function useSavedAccess(access:SoulAccess|null,setAccess:(a:SoulAccess)=>void){
  useEffect(()=>{
    async function restore(){
      let stored:SoulAccess|null=null;
      try{const value=JSON.parse(localStorage.getItem('soullink-access')||'null');if(valid(value))stored=value;}catch{}
      const q=new URLSearchParams(location.hash.slice(1));
      if(q.has('room')&&token(q.get('key'))){
        const next:SoulAccess={id:q.get('room')!,readToken:q.get('key')!};
        if(stored?.id===next.id&&stored.readToken===next.readToken)Object.assign(next,stored);
        const role=q.get('player'),write=q.get('playerKey');
        if((role==='John'||role==='Eddie')&&token(write))next[role]=write;
        if(valid(next))setAccess(next);
      }else{
        try{const response=await fetch('/api/account');if(response.status===401){location.reload();return;}const result:any=await response.json();if(valid(result.access)){setAccess(result.access);return;}}catch{}
        if(stored)setAccess(stored);
      }
    }
    restore();window.addEventListener('hashchange',restore);return()=>window.removeEventListener('hashchange',restore);
  },[setAccess]);
  useEffect(()=>{if(access)try{localStorage.setItem('soullink-access',JSON.stringify(access));}catch{}},[access]);
}

type Layout='map'|'overview'|'discord';
export function SoulOnline({access,onNew,members,now,blocked,map,children}:{access:SoulAccess|null,onNew:()=>void,members:Record<'John'|'Eddie',LiveMember>,now:number,blocked:Record<'John'|'Eddie',string[]>,map?:ReactNode,children?:ReactNode}){
  const [layout,setLayout]=useState<Layout>('map'),[wide,setWide]=useState(false);
  useEffect(()=>{try{const saved=localStorage.getItem('soullink-layout-'+access?.id) as Layout|null;setLayout(saved&&['map','overview','discord'].includes(saved)?saved:access?.Eddie&&!access?.John?'discord':'map');setWide(localStorage.getItem('soullink-discord-wide')==='true');}catch{setLayout(access?.Eddie&&!access?.John?'discord':'map');}},[access?.id,access?.Eddie,access?.John]);
  function chooseLayout(next:Layout){setLayout(next);try{localStorage.setItem('soullink-layout-'+access?.id,next);}catch{}}
  const [pair,setPair]=useState(''),[message,setMessage]=useState(''),[busy,setBusy]=useState(false);
  useEffect(()=>{const read=()=>{const p=new URLSearchParams(location.hash.slice(1)).get('pair');if(p&&/^[a-f0-9-]{36}$/.test(p))setPair(p);};read();window.addEventListener('hashchange',read);return()=>window.removeEventListener('hashchange',read);},[]);
  async function approve(player:'John'|'Eddie'){
    if(!access?.[player])return;setBusy(true);
    try{const response=await fetch('/api/pair/approve',{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+access[player]},body:JSON.stringify({deviceId:pair,roomId:access.id,readToken:access.readToken})});const d:any=await response.json();if(!response.ok)throw Error(d.error);setPair('');setMessage(`${player==='John'?'Anakin':'Obi-Wan'} verbunden. Du kannst zur App zurückkehren.`);location.hash=new URLSearchParams({room:access.id,key:access.readToken}).toString();}
    catch(e){setMessage((e as Error).message);}finally{setBusy(false);}
  }
  async function invite(){
    if(!access?.Eddie)return;
    const link=location.origin+'/#'+new URLSearchParams({room:access.id,key:access.readToken,player:'Eddie',playerKey:access.Eddie});
    try{await navigator.clipboard.writeText(link);setMessage('Privater Spielerlink kopiert. Nur an Eddie weitergeben; damit kann er Obi-Wan verbinden.');}
    catch{setMessage('Kopieren nicht möglich. Bitte den Browserzugriff auf die Zwischenablage erlauben.');}
  }
  const team=(player:'John'|'Eddie')=><article className={'team-card team-'+player.toLowerCase()} key={player}><h3>{player==='John'?'Anakin':'Obi-Wan'} <span>{player}</span></h3><LiveParty member={members[player]} player={player==='John'?'Anakin':'Obi-Wan'} now={now} blocked={blocked[player]}/></article>;
  return <>
    {pair&&<section className="online-connect"><div><h2>Deine App verbinden</h2><p>Bestätige nur, wenn du gerade in deiner eigenen App „Website verbinden“ gedrückt hast. Danach verbindet sie sich automatisch. John spielt Anakin, Eddie spielt Obi-Wan.</p></div>{!access?<p>Erstellt zuerst eine gemeinsame Runde. Nach dem Anmelden finden John und Eddie automatisch dieselbe Runde.</p>:<div className="online-actions">{access.John&&<button disabled={busy} onClick={()=>approve('John')}>Diese App ist Anakin</button>}{access.Eddie&&<button disabled={busy} onClick={()=>approve('Eddie')}>Diese App ist Obi-Wan</button>}{!access.John&&!access.Eddie&&<button onClick={()=>{location.hash='';location.reload();}}>Eigenen Spielerzugang laden</button>}</div>}</section>}
    {message&&<p className="online-message" role="status">{message}</p>}
    {access&&<><section className="online-controls"><div><h2>Eure Spielübersicht</h2><p>Jeder Browser merkt sich seine eigene Ansicht. Die Karte bleibt in allen Ansichten erreichbar.</p></div><div className="online-actions layout-actions" aria-label="Ansicht auswählen"><button aria-pressed={layout==='map'} onClick={()=>chooseLayout('map')}>Karte mittig</button><button aria-pressed={layout==='overview'} onClick={()=>chooseLayout('overview')}>Fangbuch groß</button><button aria-pressed={layout==='discord'} onClick={()=>chooseLayout('discord')}>Discord-Platz</button><button onClick={()=>{if(confirm('Eine neue gemeinsame Website-Runde erstellen? Die bisherige Runde bleibt erhalten.'))onNew();}}>Neue Runde</button><button onClick={async()=>{await fetch('/api/logout',{method:'POST'});localStorage.removeItem('soullink-access');location.href='/';}}>Abmelden</button></div></section>
    <div className={'session-workspace layout-'+layout+(layout==='discord'?' with-discord':'')+(wide?' discord-wide':'')}>
      <div className="session-content">{layout==='map'?<section className="map-dashboard" aria-label="Teams und permanente Karte">{team('John')}<div className="map-center">{map}</div>{team('Eddie')}</section>:<><section className="team-overview" aria-label="Eure aktuellen Teams">{team('John')}{team('Eddie')}</section>{map}</>}{children}</div>
      {layout==='discord'&&<aside className="discord-dock" aria-label="Platzhalter für Discord"><div className="discord-dock-title"><strong>Platz für Discord</strong><button aria-pressed={wide} onClick={()=>{setWide(!wide);try{localStorage.setItem('soullink-discord-wide',String(!wide));}catch{}}}>{wide?'Schmaler':'Breiter'}</button></div><div className="discord-surface"><span>DISCORD</span><h3>Das Fenster gehört euch.</h3><p>Discord-Übertragung als eigenes Fenster öffnen und hier darüberlegen.</p><small>Nur reservierter Platz · kein Stream, kein Upload</small></div><p className="discord-hint">Höhe an der unteren rechten Ecke anpassen. Discord bleibt ein separates Fenster; diese Seite bettet es nicht ein.</p></aside>}
    </div></>}

  </>;
}
