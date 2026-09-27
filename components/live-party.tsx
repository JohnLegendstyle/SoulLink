export type LiveMon={uid:string,species:number,nickname:string,level:number|null,hp:number|null,maxHp:number|null};
export type LiveMember={party:LiveMon[],teamSource?:string,teamCapturedAt?:number};
export function LiveParty({member,player,now,blocked}:{member:LiveMember,player:string,now:number,blocked:string[]}){
  const live=member.teamSource==='live'&&!!member.teamCapturedAt&&now-member.teamCapturedAt<60000;
  return <aside className="live-party" aria-label={`Aktuelles Team von ${player}`}><div className="live-party-heading"><strong>Aktuelles Team</strong><span>{live?`Live · vor ${Math.max(0,Math.round((now-member.teamCapturedAt!)/1000))} s`:member.teamSource==='live'?'Letzter Live-Stand · veraltet':'Letzter Speicherstand'}</span></div>
    <ol>{Array.from({length:6},(_,i)=>{const mon=member.party[i];const locked=!!mon&&blocked.includes(mon.uid);return <li key={mon?.uid||`empty-${i}`} className={locked?'party-locked':''}>{mon?<><img src={`https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/${mon.species}.png`} width="64" height="64" alt={`Pokémon #${mon.species}`} referrerPolicy="no-referrer"/><div><strong>{mon.nickname||`Pokémon #${mon.species}`}</strong><span>Lv. {mon.level??'?'}{locked?' · Gesperrt':''}</span>{mon.maxHp!=null&&<><meter min={0} max={mon.maxHp} value={mon.hp??0} aria-label={`${mon.hp??0} von ${mon.maxHp} KP`}/><small>{mon.hp??0} / {mon.maxHp} KP</small></>}</div></>:<><b className="party-slot">{i+1}</b><span>Freier Teamplatz</span></>}</li>;})}</ol>
    {!member.party.length&&<p>Noch kein Team übertragen.</p>}
  </aside>;
}
