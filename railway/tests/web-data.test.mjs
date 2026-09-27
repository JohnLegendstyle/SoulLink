import test from 'node:test';
import assert from 'node:assert/strict';
import {typeInfo} from '../../lib/pokemon-types.mjs';
import {mapSections} from '../../lib/map-sections.mjs';

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
