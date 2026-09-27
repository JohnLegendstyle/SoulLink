// Original, code-drawn artwork inspired by handheld region maps; no ROM artwork.
export function RegionTerrain({region}:{region:'Johto'|'Kanto'}){
  const johto=region==='Johto';
  const land=johto
    ?'M30 180H90V120H180V75H270V30H820V465H745V495H610V465H525V525H430V555H310V510H270V420H285V345H240V285H180V240H90V510H30Z'
    :'M45 60H255V35H630V75H795V330H750V465H690V540H375V555H330V495H240V450H150V360H105V270H45Z';
  const woods=johto?[[310,300,110,75],[310,450,55,90],[490,250,65,120],[590,330,65,65],[90,155,110,65]]:[[135,160,85,105],[285,180,110,55],[525,190,120,55],[540,440,100,55]];
  return <g shapeRendering="crispEdges" aria-hidden="true">
    <defs>
      <pattern id="region-sea" width="30" height="30" patternUnits="userSpaceOnUse"><rect width="30" height="30" fill="#78bcdd"/><path d="M3 18H12V15H21" fill="none" stroke="#9dd2e5" strokeWidth="3"/></pattern>
      <pattern id="region-grass" width="15" height="15" patternUnits="userSpaceOnUse"><rect width="15" height="15" fill="#b9d995"/><path d="M3 9H6V6M12 3V6" fill="none" stroke="#acce88" strokeWidth="2"/></pattern>
      <pattern id="region-trees" width="18" height="21" patternUnits="userSpaceOnUse"><path d="M3 15V9H6V3H12V9H15V15Z" fill="#53976a"/><path d="M6 9V6H9V3H12V12H6Z" fill="#75b777"/><path d="M9 15V18" stroke="#698554" strokeWidth="3"/></pattern>
    </defs>
    <rect width="860" height="640" fill="url(#region-sea)"/>
    <path d={land} transform="translate(0 9)" fill="#488d9d" stroke="#488d9d" strokeWidth="15"/>
    <path d={land} fill="url(#region-grass)" stroke="#e6e3b1" strokeWidth="12"/>
    {woods.map(([x,y,w,h],i)=><rect key={i} x={x} y={y} width={w} height={h} fill="url(#region-trees)"/>)}
    {(johto?[[445,45],[600,65],[655,80],[750,210],[755,255]]:[[65,85],[75,160],[315,70],[660,80],[710,100]]).map(([x,y],i)=><g key={i} transform={`translate(${x} ${y})`}><path d="M-24 27V15H-15V0H-6V-12H6V0H15V15H24V27Z" fill="#a99f79" stroke="#8f9970" strokeWidth="3"/><path d="M-15 15V3H-6V-9H3V9H12V21H-15Z" fill="#d4c699"/></g>)}
    {johto?<><path d="M530 35H570V75H530Z" fill="#78bcdd" stroke="#e4e3ac" strokeWidth="6"/><path d="M190 395H235V435H190Z M85 410H125V450H85Z" fill="url(#region-grass)" stroke="#e6e3b1" strokeWidth="6"/></>:<path d="M165 555H215V590H165Z M340 555H380V590H340Z" fill="url(#region-grass)" stroke="#e6e3b1" strokeWidth="6"/>}
    <rect x="18" y="590" width="230" height="34" fill="#f5edce" stroke="#648776" strokeWidth="3"/>
    <text x="33" y="613" fill="#35594e" fontSize="19" fontFamily="monospace" fontWeight="bold" letterSpacing="3">{region.toUpperCase()}</text>
    <text x="835" y="618" fill="#254f64" fontSize="11" textAnchor="end">REGIONSKARTE · STILISIERTE LAGE</text>
  </g>;
}
