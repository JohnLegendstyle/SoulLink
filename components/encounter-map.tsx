'use client';
import {useState} from 'react';
import {places,routeLines,evidence,placeStatus,statusLabels,type CatchMember,type CatchStatus} from '@/lib/encounters.mjs';
import type {SoulAccess} from './soul-online';
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
        <defs><pattern id="map-grid" width="30" height="30" patternUnits="userSpaceOnUse"><path d="M30 0H0V30" fill="none" stroke="#9ed9ca" strokeOpacity=".045"/></pattern></defs>
        <rect width="860" height="640" fill="#102630"/><path d="M15 60Q180 15 330 55T840 60V445Q750 405 710 555L300 620 235 520 35 545Z" fill="#1a3939"/>
        <path d="M310 35L390 135 470 35 550 155 655 40 805 155" fill="none" stroke="#2a4845" strokeWidth="35" strokeLinejoin="round"/>
        <rect width="860" height="640" fill="url(#map-grid)"/>
        <text x="25" y="610" fill="#8eb6b8" fontSize="18" letterSpacing="5">{region.toUpperCase()}</text><text x="835" y="615" fill="#9db2b7" fontSize="11" textAnchor="end">SCHEMATISCH · NICHT MASSSTABSGETREU</text>
        {routeLines[region].map((line,i)=><polyline key={i} points={line.map(id=>places.find(p=>p.id===id)).filter(Boolean).map(p=>`${p!.x},${p!.y}`).join(' ')} fill="none" stroke="#496265" strokeWidth="6" strokeLinejoin="round"/>)}
        {visible.map(p=>{const a=placeStatus(members.John,p.id),b=placeStatus(members.Eddie,p.id);return <g key={p.id} role="button" tabIndex={0} aria-label={`${p.name}. Anakin: ${statusLabels[a]}. Obi-Wan: ${statusLabels[b]}`} aria-pressed={selected===p.id} onClick={()=>setSelected(p.id)} onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();setSelected(p.id);}}} className="catch-node" transform={`translate(${p.x} ${p.y})`}>
          <circle r="18" fill="#0e2029" stroke={selected===p.id?'#fff0bd':'#38545b'} strokeWidth={selected===p.id?3:1}/><path d="M-1 -12A12 12 0 0 0 -1 12Z" fill={colors[a]}/><path d="M1 -12A12 12 0 0 1 1 12Z" fill={colors[b]}/>
          <text y={p.id>=149&&p.id<=196?4:31} textAnchor="middle" fill={p.id>=149&&p.id<=196?'#07151a':'#e5eddf'} fontSize={p.id>=149&&p.id<=196?12:10} fontWeight="bold" paintOrder="stroke" stroke={p.id>=149&&p.id<=196?'none':'#102630'} strokeWidth="3">{p.name.replace('Route ','')}</text>
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
