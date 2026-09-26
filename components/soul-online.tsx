'use client';
import {useEffect,useRef,useState} from 'react';
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
  const canvas=useRef<HTMLCanvasElement>(null);
  const [retry,setRetry]=useState(0),[connection,setConnection]=useState('Verbinde …');
  const [live,setLive]=useState(false),[fps,setFPS]=useState({target:0,received:0,shown:0});
  useEffect(()=>{
    let active=true,controller:AbortController|null=null,animation=0;
    const encoded:{bytes:Uint8Array<ArrayBuffer>,due:number}[]=[],decoded:{image:ImageBitmap,due:number}[]=[];
    let decoding=false,visible=false,generation=0,lastDue=0;
    let target=0,received=0,shown=0,lastFrame=0,lastStats=performance.now(),lastPacket=performance.now();
    function offline(){generation++;encoded.length=0;for(const f of decoded)f.image.close();decoded.length=0;lastDue=0;if(visible){visible=false;setLive(false);}}
    async function decode(){
      if(decoding)return;decoding=true;
      try{while(active&&encoded.length){
        const frame=encoded.shift()!;const epoch=generation;
        const next=await createImageBitmap(new Blob([frame.bytes],{type:'image/jpeg'}));
        if(!active||epoch!==generation){next.close();continue;}
        decoded.push({image:next,due:frame.due});if(decoded.length>32)decoded.shift()!.image.close();
      }}catch{}finally{decoding=false;}
    }
    function draw(){
      if(!active)return;
      let next:ImageBitmap|null=null;
      while(decoded.length&&decoded[0].due<=performance.now()){next?.close();next=decoded.shift()!.image;}
      if(next&&canvas.current&&!document.hidden){
        const surface=canvas.current;
        if(surface.width!==next.width||surface.height!==next.height){surface.width=next.width;surface.height=next.height;}
        surface.getContext('2d',{alpha:false})?.drawImage(next,0,0);next.close();shown++;
        if(!visible){visible=true;setLive(true);}
      }else next?.close();
      animation=requestAnimationFrame(draw);
    }
    async function connect(){
      while(active){
        if(document.hidden){await new Promise(r=>setTimeout(r,250));continue;}
        controller=new AbortController();
        lastPacket=performance.now();
        try{
          const result=await fetch('/api/live?'+new URLSearchParams({id:access.id,player}),{headers:{Authorization:'Bearer '+access.readToken},cache:'no-store',signal:controller.signal});
          if(!result.ok||!result.body){setConnection(result.status===401?'Zugang abgelaufen – Website neu anmelden':'Verbindung wird wiederhergestellt …');throw Error('Stream unavailable');}
          const reader=result.body.getReader();let pending:Uint8Array<ArrayBufferLike>=new Uint8Array(0);
          try{while(active){
            const {value,done}=await reader.read();if(done)break;
            lastPacket=performance.now();
            if(pending.length+value.length>4000000)throw Error('Frame buffer limit');
            const buffer=new Uint8Array(pending.length+value.length);buffer.set(pending);buffer.set(value,pending.length);pending=buffer;
            while(pending.length>=8){
              const header=new DataView(pending.buffer,pending.byteOffset,8),size=header.getUint32(0),configured=header.getUint16(4),kind=header.getUint16(6);
              if(size>300000||configured>1000||kind>2)throw Error('Invalid frame');
              if(pending.length<size+8)break;
              if(kind===1&&size){
                const now=performance.now();if(target!==configured)lastDue=0;
                target=configured;received++;lastFrame=now;
                setConnection('Verbunden');
                // A short bounded playout buffer smooths TCP packet bursts; it
                // never fabricates frames or grows into a delayed recording.
                lastDue=Math.min(now+150,Math.max(now+50,lastDue+(configured?1000/configured:0)));
                encoded.push({bytes:pending.slice(8,size+8) as Uint8Array<ArrayBuffer>,due:lastDue});
                // Keep enough frames for the 150 ms playout window at 120 FPS.
                // A shorter queue discards frames before they become due.
                if(encoded.length>32)encoded.shift();
              }
              else if(kind===0&&performance.now()-lastFrame>8000){offline();setConnection('Warte auf Spielbild aus der App');}
              pending=pending.subarray(size+8);
            }
            void decode();
          }}finally{await reader.cancel().catch(()=>{});reader.releaseLock();}
        }catch{}finally{controller?.abort();controller=null;}
        if(active)await new Promise(r=>setTimeout(r,250));
      }
    }
    const visibility=()=>{if(document.hidden)controller?.abort();};
    document.addEventListener('visibilitychange',visibility);
    const stats=setInterval(()=>{
      const now=performance.now(),seconds=(now-lastStats)/1000;
      setFPS({target,received:Math.round(received/seconds),shown:Math.round(shown/seconds)});received=shown=0;lastStats=now;
      if(lastFrame&&now-lastFrame>3000)setConnection('Verbindung wird wiederhergestellt …');
      if(now-lastFrame>8000)offline();
      if(controller&&now-lastPacket>8000)controller.abort();
    },1000);
    draw();void connect();
    return()=>{active=false;controller?.abort();cancelAnimationFrame(animation);clearInterval(stats);document.removeEventListener('visibilitychange',visibility);for(const f of decoded)f.image.close();decoded.length=0;encoded.length=0;};
  },[access.id,access.readToken,player,retry]);
  return <article className="game-preview"><div className="preview-title"><strong>{player==='John'?'Anakin':'Obi-Wan'}</strong><span className={live&&connection==='Verbunden'?'is-live':''}>{live&&connection==='Verbunden'?'● Live · App: '+(fps.target?fps.target+' FPS':'unbegrenzt'):connection}</span></div><div className="preview-screen"><canvas ref={canvas} style={{display:live?'block':'none',maxWidth:'100%',maxHeight:'100%',objectFit:'contain'}} aria-label={`DS-Bildschirme von ${player==='John'?'Anakin':'Obi-Wan'}`}/>{!live&&<p>In der App „Übertragung starten“ einschalten.<br/>Spielfenster nicht minimieren. Kein Speichern nötig.<br/>Privat und ohne Ton.</p>}</div><p style={{padding:'8px 16px',fontSize:12,color:'#a4adbd',margin:0}}>Empfangen: {live?fps.received:0} FPS · Angezeigt: {live?fps.shown:0} FPS<br/>Anzeige abhängig von Bildschirm, Browser und Verbindung.</p><button onClick={()=>{setConnection('Verbinde …');setRetry(x=>x+1);}}>Bild neu verbinden</button></article>;
}

export function SoulOnline({access,onNew}:{access:SoulAccess|null,onNew:()=>void}){
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
  return <>
    {pair&&<section className="online-connect"><div><h2>Deine App verbinden</h2><p>Bestätige nur, wenn du gerade in deiner eigenen App „Website verbinden“ gedrückt hast. Danach verbindet sie sich automatisch. John spielt Anakin, Eddie spielt Obi-Wan.</p></div>{!access?<p>Erstellt zuerst eine gemeinsame Runde. Nach dem Anmelden finden John und Eddie automatisch dieselbe Runde.</p>:<div className="online-actions">{access.John&&<button disabled={busy} onClick={()=>approve('John')}>Diese App ist Anakin</button>}{access.Eddie&&<button disabled={busy} onClick={()=>approve('Eddie')}>Diese App ist Obi-Wan</button>}{!access.John&&!access.Eddie&&<button onClick={()=>{location.hash='';location.reload();}}>Eigenen Spielerzugang laden</button>}</div>}</section>}
    {message&&<p className="online-message" role="status">{message}</p>}
    {access&&<><section className="online-controls"><div><h2>Eure Bildschirme</h2><p>FPS folgen der App-Einstellung · ohne Ton · nur die DS-Bildschirme. Die tatsächlichen Empfangs- und Anzeige-FPS stehen unter dem Bild. Mehr FPS benötigen mehr Upload und Datenvolumen.</p></div><div className="online-actions"><button onClick={()=>{if(confirm('Eine neue gemeinsame Website-Runde erstellen? Die bisherige Runde bleibt erhalten.'))onNew();}}>Neue Website-Runde</button><button onClick={async()=>{await fetch('/api/logout',{method:'POST'});localStorage.removeItem('soullink-access');location.href='/';}}>Abmelden</button></div></section><section className="game-previews"><GamePreview access={access} player="John"/><GamePreview access={access} player="Eddie"/></section></>}
  </>;
}
