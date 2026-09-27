import {test} from 'node:test';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {DatabaseSync} from 'node:sqlite';
import {crc16,pokemonReport,reports,enrichMember,backfillEncounters} from '../save-encounters.mjs';
const python=process.env.SOULLINK_TEST_PYTHON||'python3';
const fixtures=JSON.parse(execFileSync(python,['-c',`import sys,json
sys.path[:0]=['desktop','desktop/tests']
from test_encounters import synthetic
from soullink.save_reader import _pokemon
print(json.dumps([{'hex':synthetic(i).hex(),'expected':_pokemon(synthetic(i),True).api()} for i in range(24)]))`],{encoding:'utf8'}));
function save(raw){
  const data=Buffer.alloc(0x80000);
  for(const base of [0,0x40000]){
    for(const [i,c] of [...'Anakin'].entries())data.writeUInt16LE(c===c.toUpperCase()?0x12b+c.charCodeAt(0)-65:0x145+c.charCodeAt(0)-97,base+0x64+i*2);
    data[base+0x94]=1;raw.copy(data,base+0x98);
    data.writeUInt16LE(crc16(data.subarray(base,base+0xf628-16)),base+0xf628-2);
    const s=base+0xf700;data.writeUInt16LE(crc16(data.subarray(s,s+0x12310-16)),s+0x12310-2);
  }
  return data;
}
test('server report reader matches desktop reader for all 24 block orders',()=>{
  for(const f of fixtures){const got=pokemonReport(Buffer.from(f.hex,'hex'));
    for(const k of ['uid','metLocation','originGame','isEgg','eggLocation'])assert.equal(got[k],f.expected[k]);}
  const bad=Buffer.from(fixtures[0].hex,'hex');bad[20]^=255;assert.equal(pokemonReport(bad),null);
});
test('cloud backfill enriches known IDs only and never alters saves, party, KO or manual marks',()=>{
  const bytes=save(Buffer.from(fixtures[0].hex,'hex')),copy=Buffer.from(bytes),found=reports(bytes,'John');
  assert.equal(found.size,1);assert.throws(()=>reports(bytes,'Eddie'));
  const uid=fixtures[0].expected.uid;
  const member={seen:[{uid,nickname:'T1',species:25}],party:[{uid,hp:3}],dead:[uid],encounters:{177:{status:'missed'}}};
  const db=new DatabaseSync(':memory:');db.exec('CREATE TABLE rooms(id TEXT,state TEXT,revision INTEGER); CREATE TABLE cloud_versions(room TEXT,role TEXT,revision INTEGER,data BLOB)');
  db.prepare('INSERT INTO rooms VALUES(?,?,0)').run('room',JSON.stringify({John:member,Eddie:{seen:[{uid}],party:[]},names:{0:'Link'}}));
  db.prepare('INSERT INTO cloud_versions VALUES(?,?,?,?)').run('room','John',1,bytes);
  assert.equal(backfillEncounters(db),2);assert.equal(backfillEncounters(db),0);
  const state=JSON.parse(db.prepare('SELECT state FROM rooms').get().state);
  assert.equal(state.John.seen[0].metLocation,177);assert.equal(state.John.party[0].hp,3);
  assert.equal(state.Eddie.seen[0].metLocation,undefined);assert.equal(state.John.encounters[177].status,'missed');assert.deepEqual(state.John.dead,[uid]);
  assert.deepEqual(Buffer.from(db.prepare('SELECT data FROM cloud_versions').get().data),copy);
  const unknown={seen:[{uid:'not-in-save'}]};assert.equal(enrichMember(unknown,found),0);db.close();
});
