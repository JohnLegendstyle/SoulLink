// HGSS map-section IDs: pret/pokeheartgold/include/constants/map_sections.h.
// Layout is a hand-authored schematic, not extracted Nintendo map artwork.
export const places = [
  [126,'Neuborkia','Johto',680,420],[127,'Rosalia City','Johto',540,420],
  [128,'Viola City','Johto',470,230],[129,'Azalea City','Johto',390,510],
  [130,'Anemonia City','Johto',110,430],[131,'Dukatia City','Johto',290,375],
  [132,'Oliviana City','Johto',215,260],[133,'Teak City','Johto',360,150],
  [134,'Mahagonia City','Johto',550,150],[135,'See des Zorns','Johto',550,55],
  [136,'Ebenholz City','Johto',720,170],[137,'Silberberg','Johto',800,345],
  [138,'Alabastia','Kanto',190,410],[139,'Vertania City','Kanto',190,305],
  [140,'Marmoria City','Kanto',190,130],[141,'Azuria City','Kanto',490,125],
  [142,'Lavandia','Kanto',710,280],[143,'Orania City','Kanto',490,400],
  [144,'Prismania City','Kanto',325,280],[145,'Fuchsania City','Kanto',420,515],
  [146,'Zinnoberinsel','Kanto',190,575],[147,'Indigo-Plateau','Kanto',75,130],
  [148,'Saffronia City','Kanto',490,280],
  ...[[1,190,355],[2,190,220],[3,265,130],[4,405,125],[5,490,200],
    [6,490,345],[7,405,280],[8,610,280],[9,600,125],[10,710,190],
    [11,600,400],[12,710,365],[13,710,480],[14,620,515],[15,525,515],
    [16,260,280],[17,260,400],[18,320,515],[19,420,575],[20,310,575],
    [21,190,495],[22,100,305],[24,490,55],[25,595,55],[26,790,425],
    [27,690,510],[28,100,410]].map(([n,x,y])=>[148+n,`Route ${n}`,'Kanto',x,y]),
  ...[[29,610,420],[30,540,335],[31,540,230],[32,470,340],[33,440,510],
    [34,290,455],[35,290,280],[36,395,230],[37,360,195],[38,280,150],
    [39,215,200],[40,150,295],[41,150,370],[42,460,150],[43,550,105],
    [44,625,150],[45,720,290],[46,680,360],[47,65,430],[48,65,340]]
    .map(([n,x,y])=>[148+n,`Route ${n}`,'Johto',x,y]),
  [197,'Digda-Höhle','Kanto',270,200],[198,'Mondberg','Kanto',330,125],
  [199,'Azuria-Höhle','Kanto',425,80],[200,'Felstunnel','Kanto',710,125],
  [201,'Kraftwerk','Kanto',775,190],[202,'Safari-Zone','Johto',65,270],
  [203,'Seeschauminseln','Kanto',360,575],[204,'Knofensa-Turm','Johto',470,170],
  [205,'Glockenturm','Johto',395,80],[206,'Turmruine','Johto',325,80],
  [207,'Nationalpark','Johto',290,230],[208,'Radioturm','Johto',220,375],
  [209,'Alph-Ruinen','Johto',400,290],[210,'Einheitstunnel','Johto',470,450],
  [211,'Flegmon-Brunnen','Johto',390,560],[212,'Leuchtturm','Johto',255,320],
  [213,'Rocket-Versteck','Johto',610,210],[214,'Steineichenwald','Johto',315,510],
  [215,'Dukatia-Passage','Johto',230,445],[216,'Kesselberg','Johto',465,85],
  [217,'Eispfad','Johto',705,95],[218,'Strudelinseln','Johto',215,415],
  [219,'Silberberghöhle','Johto',790,285],[220,'Dunkelhöhle','Johto',620,280],
  [221,'Siegesstraße','Kanto',75,215],[222,'Drachenhöhle','Johto',785,115],
  [223,'Tohjo-Fälle','Johto',790,420],[224,'Vertania-Wald','Kanto',120,220],
  [225,'Pokéathlon','Johto',225,230],[226,'M.S. Aqua','Johto',270,560],
  [227,'Safari-Eingang','Johto',65,210],[228,'Felsklippengrotte','Johto',65,500],
  [229,'Kampfzonenzugang','Johto',145,210],[230,'Glockenklangpfad','Johto',395,115],
  [231,'Sinjoh-Ruinen','Johto',790,55],[232,'Felsenherzturm','Johto',115,550],
  [234,'Klippenpassage','Johto',110,485],
].map(([id,name,region,x,y])=>({id,name,region,x,y}));
export const placeIds=new Set(places.map(p=>p.id));
export const routeLines={
  Johto:[[126,177,127,178,179,128,180,210,181,129,214,182,131,183,207,184,128],
    [184,185,133,186,187,132,188,189,130,195,196,202],
    [133,190,134,191,135],[134,192,217,136,193,194,177],[136,222],[126,223],[137,219]],
  Kanto:[[138,149,139,150,140,151,198,152,141,153,148,154,143],
    [141,172,173],[141,157,200,158,142,156,148,155,144,164,165,166,145],
    [143,159,160,142],[160,161,162,163,145,167,168,146,169,138],
    [139,170,221,147],[138,176],[174,221],[175,174]],
};
export function encounterFields(v){
  const out={};
  for(const k of ['metLocation','originGame','eggLocation']){
    if(v[k]===undefined)continue;
    if(v[k]!==null&&(!Number.isInteger(v[k])||v[k]<0||v[k]>65535))throw Error('Ungültiger Fangort');
    out[k]=v[k];
  }
  if(v.isEgg!==undefined){if(typeof v.isEgg!=='boolean')throw Error('Ungültige Ei-Daten');out.isEgg=v.isEgg;}
  return out;
}
export function evidence(member,id){
  // Native HG/SS only; hatched eggs and imported Pokémon are not wild catches.
  return (member?.seen||[]).filter(m=>m.metLocation===id&&[7,8].includes(m.originGame)&&!m.isEgg&&!m.eggLocation);
}
export function placeStatus(member,id){
  const manual=member?.encounters?.[id]?.status;
  if(manual)return manual;
  return evidence(member,id).length?'caught':'unknown';
}
export const statusLabels={caught:'Fang / Erhalt erfasst',missed:'Begegnung verpasst',open:'Als offen markiert',unknown:'Kein Fang erfasst'};
