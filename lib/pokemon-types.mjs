import {pokemonTypes} from './pokemon-types-data.mjs';

export const typeNames={normal:'Normal',fighting:'Kampf',flying:'Flug',poison:'Gift',ground:'Boden',rock:'Gestein',bug:'Käfer',ghost:'Geist',steel:'Stahl',fire:'Feuer',water:'Wasser',grass:'Pflanze',electric:'Elektro',psychic:'Psycho',ice:'Eis',dragon:'Drache',dark:'Unlicht'};

const chart={
  normal:{rock:.5,ghost:0,steel:.5},
  fighting:{normal:2,flying:.5,poison:.5,rock:2,bug:.5,ghost:0,steel:2,psychic:.5,ice:2,dark:2},
  flying:{fighting:2,rock:.5,bug:2,steel:.5,grass:2,electric:.5},
  poison:{poison:.5,ground:.5,rock:.5,ghost:.5,steel:0,grass:2},
  ground:{flying:0,poison:2,rock:2,bug:.5,steel:2,fire:2,grass:.5,electric:2},
  rock:{fighting:.5,flying:2,ground:.5,bug:2,steel:.5,fire:2,ice:2},
  bug:{fighting:.5,flying:.5,poison:.5,ghost:.5,steel:.5,fire:.5,grass:2,psychic:2,dark:2},
  ghost:{normal:0,ghost:2,steel:.5,psychic:2,dark:.5},
  steel:{rock:2,steel:.5,fire:.5,water:.5,electric:.5,ice:2},
  fire:{rock:.5,bug:2,steel:2,fire:.5,water:.5,grass:2,ice:2,dragon:.5},
  water:{ground:2,rock:2,fire:2,water:.5,grass:.5,dragon:.5},
  grass:{flying:.5,poison:.5,ground:2,rock:2,bug:.5,steel:.5,fire:.5,water:2,grass:.5,dragon:.5},
  electric:{flying:2,ground:0,water:2,grass:.5,electric:.5,dragon:.5},
  psychic:{fighting:2,poison:2,steel:.5,psychic:.5,dark:0},
  ice:{flying:2,ground:2,steel:.5,fire:.5,water:.5,grass:2,ice:.5,dragon:2},
  dragon:{steel:.5,dragon:2},
  dark:{fighting:.5,ghost:2,steel:.5,psychic:2,dark:.5},
};

const all=Object.keys(typeNames);
const multiplier=(attack,defence)=>chart[attack]?.[defence]??1;

export function typeInfo(species){
  const raw=pokemonTypes[species]||['normal','normal'];
  const types=[...new Set(raw)].filter(type=>typeNames[type]);
  const weak=all.map(type=>({type,multiplier:types.reduce((value,defence)=>value*multiplier(type,defence),1)})).filter(item=>item.multiplier>1).sort((a,b)=>b.multiplier-a.multiplier||typeNames[a.type].localeCompare(typeNames[b.type],'de'));
  const strong=all.filter(defence=>types.some(attack=>multiplier(attack,defence)>1));
  return {types,weak,strong};
}
