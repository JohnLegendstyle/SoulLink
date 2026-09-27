import {test} from 'node:test';
import assert from 'node:assert/strict';
import {places,placeIds,routeLines,encounterFields,evidence,placeStatus} from '../../lib/encounters.mjs';
test('map IDs are unique and every schematic edge has a location',()=>{
  assert.equal(placeIds.size,places.length);
  for(const lines of Object.values(routeLines))for(const line of lines)for(const id of line)assert(placeIds.has(id));
  assert.equal(places.find(p=>p.id===177).name,'Route 29');
  assert.equal(places.find(p=>p.id===220).name,'Dunkelhöhle');
});
test('no evidence is unknown, eggs and foreign origins are excluded, manual mark is reversible',()=>{
  const mon={uid:'one',metLocation:177,originGame:8,eggLocation:0,isEgg:false};
  const member={seen:[mon]};assert.equal(placeStatus(member,177),'caught');assert.equal(placeStatus(member,178),'unknown');
  for(const change of [{isEgg:true},{eggLocation:2000},{originGame:10},{metLocation:null}])assert.equal(evidence({seen:[{...mon,...change}]},177).length,0);
  member.encounters={177:{status:'missed'}};assert.equal(placeStatus(member,177),'missed');delete member.encounters[177];assert.equal(placeStatus(member,177),'caught');
  assert.deepEqual(encounterFields({}),{});assert.throws(()=>encounterFields({metLocation:'177'}));assert.throws(()=>encounterFields({isEgg:'false'}));
});
