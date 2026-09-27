'use client';
import {useState} from 'react';
import {places,routeLines,evidence,placeStatus,statusLabels,type CatchMember,type CatchStatus} from '@/lib/encounters.mjs';
import type {SoulAccess} from './soul-online';
import {RegionTerrain} from './region-terrain';
const colors:Record<CatchStatus,string>={caught:'#78dab2',missed:'#ee989d',open:'#f0c979',unknown:'#4b6070'};
const players=['John','Eddie'] as const;
const names={John:'Anakin',Eddie:'Obi-Wan'};
export function EncounterMap({access,members,onChange}:{access:SoulAccess|null,members:Record<'John'|'Eddie',CatchMember>,onChange:(player:'John'|'Eddie',encounters:CatchMember['encounters'])=>void}){
  const [region,setRegion]=useState<'Johto'|'Kanto'>('Johto'),[selected,setSelected]=useState(177),[query,setQuery]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState('');
  const place=places.find(p=>p.id===selected)!;
  const visible=places.filter(p=>p.region===region);
  const unknown=players.map(p=>members[p].seen.filter(m=>!m.metLocation).length);
  async function mark(player:'John'|'Eddie',status:string){
    if(!access?.[player])return;setBusy(true);setError('');
    try{const r=await fetch('/api/encounters',{method:'PATCH',headers:{Authorization:'Bearer '+access[player],'Content-Type':'application/json'},body:JSON.stringify({id:access.id,location:selected,status})});const d=await r.json() as {error?:string,encounters:CatchMember['encounters']};if(!r.ok)throw Error(d.error||'Markierung nicht gespeichert.');onChange(player,d.encounters);}
    catch(e){setError((e as Error).message);}finally{setBusy(false);}
  }
  return <section className="catch-map" aria-labelledby="catch-title">
    <div className="catch-heading"><div><p className="eyebrow">EUER FANGBUCH</p><h2 id="catch-title">Eine Reise. Zwei Spuren.</h2><p>Wo habt ihr bereits ein Pokémon erhalten? Jeder Punkt zeigt links Anakin, rechts Obi-Wan.</p></div><div className="catch-tabs">{(['Johto','Kanto'] as const).map(r=><button key={r} aria-pressed={region===r} onClick={()=>{setRegion(r);setSelected(r==='Johto'?177:149);setQuery('');}}>{r}</button>)}</div></div>
    <div className="catch-legend">{(Object.keys(colors) as CatchStatus[]).map(s=><span key={s}><i style={{background:colors[s]}}/>{statusLabels[s]}</span>)}</div>
    <div className="catch-layout"><div className="catch-chart" tabIndex={0} aria-label="Karte horizontal verschiebbar">
      <svg viewBox="0 0 860 640" aria-label={`${region}: schematische Fangkarte`}>
        <RegionTerrain region={region}/>
        {routeLines[region].map((line,i)=>{const points=line.map(id=>places.find(p=>p.id===id)!).filter(Boolean);const d=points.map((p,j)=>j?`H${p.x}V${p.y}`:`M${p.x} ${p.y}`).join(' ');return <g key={i} shapeRendering="crispEdges"><path d={d} fill="none" stroke="#927b55" strokeWidth="12"/><path d={d} fill="none" stroke="#f6dda2" strokeWidth="6"/></g>;})}
        {visible.map(p=>{const a=placeStatus(members.John,p.id),b=placeStatus(members.Eddie,p.id);return <g key={p.id} role="button" tabIndex={0} aria-label={`${p.name}. Anakin: ${statusLabels[a]}. Obi-Wan: ${statusLabels[b]}`} aria-pressed={selected===p.id} onClick={()=>setSelected(p.id)} onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();setSelected(p.id);}}} className="catch-node" transform={`translate(${p.x} ${p.y})`}>
          <rect className="catch-marker" x="-17" y="-15" width="34" height="30" rx="2" fill="#f8f0d0" stroke={selected===p.id?'#a53f39':'#425f57'} strokeWidth={selected===p.id?4:2}/><rect x="-13" y="-11" width="12" height="22" fill={colors[a]}/><rect x="1" y="-11" width="12" height="22" fill={colors[b]}/>
          <text y={p.id>=149&&p.id<=196?4:29} textAnchor="middle" fill={p.id>=149&&p.id<=196?'#ffffff':'#263e35'} fontSize={p.id>=149&&p.id<=196?12:10} fontWeight="bold" paintOrder="stroke" stroke={p.id>=149&&p.id<=196?'#263e35':'#f5edce'} strokeWidth="3">{p.name.replace('Route ','')}</text>
        </g>;})}
      </svg>
    </div><aside className="catch-detail"><label htmlFor="catch-search">Route oder Ort suchen</label><input id="catch-search" value={query} onChange={e=>setQuery(e.target.value)} placeholder="z. B. Route 29"/><select aria-label="Ort auswählen" value={selected} onChange={e=>setSelected(Number(e.target.value))}>{visible.filter(p=>p.name.toLowerCase().includes(query.toLowerCase())||p.id===selected).map(p=><option key={p.id} value={p.id}>{p.name}</option>)}</select>
      <h3>{place.name}</h3>{players.map(player=>{const mons=evidence(members[player],selected),status=placeStatus(members[player],selected);return <div className="catch-player" key={player}><strong>{names[player]}</strong><p style={{color:colors[status]}}>{statusLabels[status]}</p>{mons.length>0&&<ul>{mons.map(m=><li key={m.uid}>{m.nickname||`Pokémon #${m.species}`}</li>)}</ul>}{mons.length>1&&<p className="catch-warning">Mehrere Pokémon von diesem Ort – Erstfang-Regel prüfen.</p>}{access?.[player]&&<label>Markierung<select disabled={busy} value={members[player].encounters?.[selected]?.status||'auto'} onChange={e=>void mark(player,e.target.value)}><option value="auto">Automatische Erkennung</option><option value="caught">Fang manuell bestätigt</option><option value="missed">Begegnung verpasst</option><option value="open">Noch offen (manuell)</option></select></label>}</div>;})}
      {error&&<p role="alert" className="catch-warning">{error}</p>}
    </aside></div>
    <p className="catch-help">Automatisch aus Fangorten in Team und Boxen; bleibt auch nach einem Teamwechsel erfasst. Geschenke und Starter können ebenfalls als Erhalt erscheinen. Eier und Pokémon aus anderen Editionen zählen nicht automatisch. Ob es die erste Begegnung war, kann daraus nicht sicher erkannt werden. Geflüchtet oder besiegt? Bitte „Begegnung verpasst“ markieren.</p>
    {(unknown[0]>0||unknown[1]>0)&&<p className="catch-help">Noch ohne Fangort: Anakin {unknown[0]}, Obi-Wan {unknown[1]}. App 0.10 oder neuer überträgt die Orte vorhandener Pokémon beim nächsten Team-/Speicherabgleich. „Kein Fang erfasst“ bedeutet nicht automatisch „noch frei“.</p>}
  </section>;
}
