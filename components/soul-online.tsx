'use client';
import {useEffect,useState} from 'react';
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

function GamePreview({access,player}:{access:SoulAccess,player:'John'|'Eddie'}){
  const [frame,setFrame]=useState(''),[live,setLive]=useState(false);
  useEffect(()=>{
    let active=true,url='',timer:ReturnType<typeof setTimeout>,lastSuccess=0;
    const controller=new AbortController();
    async function poll(){
      try{
        if(document.hidden){setLive(false);return;}
        const result=await fetch('/api/frame?'+new URLSearchParams({id:access.id,player}),{headers:{Authorization:'Bearer '+access.readToken},cache:'no-store',signal:controller.signal});
        if(result.status===200){
          const blob=await result.blob();if(!active)return;
          const next=URL.createObjectURL(blob);if(url)URL.revokeObjectURL(url);url=next;
          lastSuccess=Date.now();setFrame(next);setLive(true);
        }else{setLive(false);setFrame('');if(url){URL.revokeObjectURL(url);url='';}}
      }catch{if(active&&Date.now()-lastSuccess>6000){setLive(false);setFrame('');}}
      finally{if(active)timer=setTimeout(poll,500);}
    }
    poll();return()=>{active=false;controller.abort();clearTimeout(timer);if(url)URL.revokeObjectURL(url);};
  },[access.id,access.readToken,player]);
  return <article className="game-preview"><div className="preview-title"><strong>{player==='John'?'Optimus':'Bee'}</strong><span className={live?'is-live':''}>{live?'● Live-Vorschau':'Nicht am Übertragen'}</span></div><div className="preview-screen">{frame&&live?<img src={frame} alt={`Die beiden DS-Bildschirme von ${player==='John'?'Optimus':'Bee'}`}/>:<p>Spiel in der verbundenen App starten.<br/>Die Vorschau ist privat und ohne Ton.</p>}</div></article>;
}

export function SoulOnline({access,onNew}:{access:SoulAccess|null,onNew:()=>void}){
  const [pair,setPair]=useState(''),[message,setMessage]=useState(''),[busy,setBusy]=useState(false);
  useEffect(()=>{const read=()=>{const p=new URLSearchParams(location.hash.slice(1)).get('pair');if(p&&/^[a-f0-9-]{36}$/.test(p))setPair(p);};read();window.addEventListener('hashchange',read);return()=>window.removeEventListener('hashchange',read);},[]);
  async function approve(player:'John'|'Eddie'){
    if(!access?.[player])return;setBusy(true);
    try{const response=await fetch('/api/pair/approve',{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+access[player]},body:JSON.stringify({deviceId:pair,roomId:access.id,readToken:access.readToken})});const d:any=await response.json();if(!response.ok)throw Error(d.error);setPair('');setMessage(`${player==='John'?'Optimus':'Bee'} verbunden. Du kannst zur App zurückkehren.`);location.hash=new URLSearchParams({room:access.id,key:access.readToken}).toString();}
    catch(e){setMessage((e as Error).message);}finally{setBusy(false);}
  }
  async function invite(){
    if(!access?.Eddie)return;
    const link=location.origin+'/#'+new URLSearchParams({room:access.id,key:access.readToken,player:'Eddie',playerKey:access.Eddie});
    try{await navigator.clipboard.writeText(link);setMessage('Privater Spielerlink kopiert. Nur an Eddie weitergeben; damit kann er Bee verbinden.');}
    catch{setMessage('Kopieren nicht möglich. Bitte den Browserzugriff auf die Zwischenablage erlauben.');}
  }
  return <>
    {pair&&<section className="online-connect"><div><h2>Deine App verbinden</h2><p>Bestätige nur, wenn du gerade in deiner eigenen App „Website verbinden“ gedrückt hast. Danach verbindet sie sich automatisch. John spielt Optimus, Eddie spielt Bee.</p></div>{!access?<p>Erstellt zuerst eine gemeinsame Runde. Nach dem Anmelden finden John und Eddie automatisch dieselbe Runde.</p>:<div className="online-actions">{access.John&&<button disabled={busy} onClick={()=>approve('John')}>Diese App ist Optimus</button>}{access.Eddie&&<button disabled={busy} onClick={()=>approve('Eddie')}>Diese App ist Bee</button>}{!access.John&&!access.Eddie&&<button onClick={()=>{location.hash='';location.reload();}}>Eigenen Spielerzugang laden</button>}</div>}</section>}
    {message&&<p className="online-message" role="status">{message}</p>}
    {access&&<><section className="online-controls"><div><h2>Eure Bildschirme</h2><p>Private Vorschau · bis 4 Bilder/s · ohne Ton · kein Desktop-Streaming</p></div><div className="online-actions"><button onClick={()=>{if(confirm('Eine neue gemeinsame Website-Runde erstellen? Die bisherige Runde bleibt erhalten.'))onNew();}}>Neue Website-Runde</button><button onClick={async()=>{await fetch('/api/logout',{method:'POST'});localStorage.removeItem('soullink-access');location.href='/';}}>Abmelden</button></div></section><section className="game-previews"><GamePreview access={access} player="John"/><GamePreview access={access} player="Eddie"/></section></>}
  </>;
}
