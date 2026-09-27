import test from 'node:test';
import assert from 'node:assert/strict';
import {typeInfo} from '../../lib/pokemon-types.mjs';
import {mapSections} from '../../lib/map-sections.mjs';
import {ensureMissedSlot,placeSeen} from '../../lib/encounters.mjs';

test('HGSS types and generation-four matchups stay local and accurate',()=>{
  assert.deepEqual(typeInfo(1).types,['grass','poison']);
  assert.deepEqual(typeInfo(6).types,['fire','flying']);
  assert.equal(typeInfo(6).weak.find(item=>item.type==='rock')?.multiplier,4);
  assert.equal(typeInfo(81).weak.find(item=>item.type==='ground')?.multiplier,4);
  assert.deepEqual(typeInfo(442).weak,[]); // Spiritomb had no weakness before Fairy.
});

test('live HGSS map IDs resolve to the catch-map sections',()=>{
  assert.equal(mapSections[33],177); // Route 29
  assert.equal(mapSections[63],126); // Player house -> New Bark Town
  assert.equal(mapSections[6],230);  // Bellchime Trail
});

test('a missed partner keeps later Soul-Link pairs aligned',()=>{
  const state={John:{seen:[]},Eddie:{seen:[]}};
  const john={uid:'john-29',species:1,metLocation:177};
  assert.equal(placeSeen(state,'John',john),true);
  ensureMissedSlot(state,'Eddie',177,123);
  assert.equal(state.Eddie.seen[0].missed,true);
  assert.match(state.Eddie.seen[0].uid,/^missed:177:/);
  const eddieNext={uid:'eddie-30',species:4,metLocation:178};
  const johnNext={uid:'john-30',species:7,metLocation:178};
  placeSeen(state,'Eddie',eddieNext);placeSeen(state,'John',johnNext);
  assert.equal(state.John.seen[1].uid,'john-30');
  assert.equal(state.Eddie.seen[1].uid,'eddie-30');
});
