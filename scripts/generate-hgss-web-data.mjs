import fs from 'node:fs';
import path from 'node:path';

const root=process.argv[2];
if(!root)throw new Error('Pfad zum pret/pokeheartgold-Quellbaum fehlt.');

const personal=JSON.parse(fs.readFileSync(path.join(root,'files/poketool/personal/personal.json'),'utf8')).baseStats;
const types=personal.slice(0,494).map(entry=>entry.types.map(value=>value.replace('TYPE_','').toLowerCase()));
fs.writeFileSync(new URL('../lib/pokemon-types-data.mjs',import.meta.url),
  '// Generated from pret/pokeheartgold HGSS personal data.\nexport const pokemonTypes='+JSON.stringify(types)+';\n');

function defines(file,prefix){
  const values=new Map();
  for(const match of fs.readFileSync(file,'utf8').matchAll(new RegExp(`^#define\\s+(${prefix}[A-Z0-9_]+)\\s+(\\d+)`,'gm')))values.set(match[1],Number(match[2]));
  return values;
}
const maps=defines(path.join(root,'include/constants/maps.h'),'MAP_');
const sections=defines(path.join(root,'include/constants/map_sections.h'),'MAPSEC_');
const headers=fs.readFileSync(path.join(root,'src/data/map_headers.h'),'utf8');
const result=[];
for(const match of headers.matchAll(/\[(MAP_[A-Z0-9_]+)\]\s*=\s*\{([\s\S]*?)\n\s*\},/g)){
  const id=maps.get(match[1]);
  const sectionName=/\.mapsec\s*=\s*(MAPSEC_[A-Z0-9_]+)/.exec(match[2])?.[1];
  if(id!==undefined&&sectionName&&sections.has(sectionName))result[id]=sections.get(sectionName);
}
fs.writeFileSync(new URL('../lib/map-sections.mjs',import.meta.url),
  '// Generated from pret/pokeheartgold HGSS map headers.\nexport const mapSections='+JSON.stringify(result.map(value=>value??null))+';\n');
