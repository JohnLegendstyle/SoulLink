import {test} from 'node:test';
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {scryptSync} from 'node:crypto';
import {DatabaseSync} from 'node:sqlite';
import {mkdtempSync,readFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {validSave} from '../cloud.mjs';

test('cloud isolation, lease contention, atomic revisions, integrity, backups and restart',async()=>{
  const directory=mkdtempSync(path.join(tmpdir(),'soullink-cloud-test-'));
  const password='local-cloud-test';
  const env={...process.env,DATA_DIR:directory,PUBLIC_DIR:path.resolve('railway-dist/public'),PORT:'0',SOULLINK_LOCAL_TEST:'1',SOULLINK_PASSWORD_HASH:'cloud:'+scryptSync(password,'cloud',32).toString('hex')};
  let child,base;
  async function start(){
    child=spawn(process.execPath,['railway/server.mjs'],{env,stdio:['ignore','pipe','pipe']});
    let output='';child.stderr.on('data',b=>output+=b);
    await new Promise((resolve,reject)=>{const timeout=setTimeout(()=>reject(Error(output||'Timeout')),5000);child.stdout.on('data',b=>{const m=String(b).match(/SoulLink ready (\d+)/);if(m){base='http://127.0.0.1:'+m[1];clearTimeout(timeout);resolve();}});child.once('exit',()=>{clearTimeout(timeout);reject(Error(output));});});
  }
  async function stop(){if(child.exitCode!==null)return;await new Promise(resolve=>{child.once('exit',resolve);child.kill();});}
  async function call(route,{method='GET',data,cookie,token}={}){
    const headers={'Content-Type':'application/json'};if(cookie)headers.Cookie=cookie;if(token)headers.Authorization='Bearer '+token;
    return fetch(base+route,{method,headers,body:data===undefined?undefined:JSON.stringify(data)});
  }
  async function login(user){const r=await call('/api/login',{method:'POST',data:{username:user,password}});assert.equal(r.status,200);return r.headers.get('set-cookie').split(';')[0];}
  try{
    await start();const john=await login('John'),eddie=await login('Eddie');
    const room=await (await call('/api/room',{method:'POST',cookie:john,data:{}})).json();
    const bee=(await (await call('/api/account',{cookie:eddie})).json()).access;
    const url='/api/cloud-save?id='+room.id,leaseUrl='/api/cloud-save/lease?id='+room.id;
    const one={romHash:'a'.repeat(64),lease:'1'.repeat(64)},two={...one,lease:'2'.repeat(64)};
    const payload=readFileSync('desktop/randomizer/checkpoints/Optimus.sav');
    assert(validSave(payload,'John'));assert(!validSave(payload,'Eddie'));
    const corrupt=Buffer.from(payload);corrupt[30]^=1;corrupt[0x40000+30]^=1;assert(!validSave(corrupt,'John'));
    assert.equal((await call(url)).status,403);
    assert.equal((await call(url,{token:room.readToken})).status,403);
    assert.equal((await call(leaseUrl,{method:'POST',token:room.John,data:one})).status,200);
    assert.equal((await call(leaseUrl,{method:'POST',token:room.John,data:two})).status,423);
    assert.equal((await call(leaseUrl,{method:'POST',token:room.John,data:{...one,romHash:'b'.repeat(64)}})).status,409);
    assert.equal((await call(url,{method:'PUT',token:room.John,data:{...one,baseRevision:0,data:corrupt.toString('base64')}})).status,400);
    let r=await call(url,{method:'PUT',token:room.John,data:{...one,baseRevision:0,data:payload.toString('base64')}});assert.equal(r.status,200);assert.equal((await r.json()).current.revision,1);
    r=await call(url,{method:'PUT',token:room.John,data:{...one,baseRevision:0,data:payload.toString('base64')}});assert.equal((await r.json()).current.revision,1);
    assert.equal((await call(url+'&revision=1',{token:bee.Eddie})).status,404);
    assert.equal((await (await call(url,{token:bee.Eddie})).json()).current,null);
    assert.equal((await call(url,{method:'PUT',token:room.John,data:{...two,baseRevision:1,data:payload.toString('base64')}})).status,423);
    const changed=Buffer.from(payload);changed[changed.length-1]^=1;
    assert.equal((await call(url,{method:'PUT',token:room.John,data:{...one,baseRevision:0,data:changed.toString('base64')}})).status,409);
    const race=await Promise.all([call(url,{method:'PUT',token:room.John,data:{...one,baseRevision:1,data:changed.toString('base64')}}),call(url,{method:'PUT',token:room.John,data:{...one,baseRevision:1,data:Buffer.from(payload.map((b,i)=>i===payload.length-2?b^1:b)).toString('base64')}})]);
    assert.deepEqual(race.map(r=>r.status).sort(),[200,409]);
    const old=await (await call(url+'&revision=1',{token:room.John})).json();assert.equal(old.data,payload.toString('base64'));
    await call(leaseUrl,{method:'POST',token:room.John,data:{...two,release:true}});
    assert.equal((await call(leaseUrl,{method:'POST',token:room.John,data:two})).status,423);
    await call(leaseUrl,{method:'POST',token:room.John,data:{...one,release:true}});
    assert.equal((await call(leaseUrl,{method:'POST',token:room.John,data:two})).status,200);
    await stop();await start();
    const persisted=await (await call(url,{token:room.John})).json();assert.equal(persisted.current.revision,2);assert.equal(persisted.versions.length,2);
    assert.equal((await call(leaseUrl,{method:'POST',token:room.John,data:one})).status,423);
    for(let revision=3;revision<=12;revision++){
      const bytes=Buffer.from(payload);bytes[bytes.length-1]=revision;
      r=await call(url,{method:'PUT',token:room.John,data:{...two,baseRevision:revision-1,data:bytes.toString('base64')}});assert.equal(r.status,200);
    }
    const retained=await (await call(url,{token:room.John})).json();assert.equal(retained.versions.length,10);assert.equal(retained.versions[0].revision,12);
    assert.equal((await call(url+'&revision=1',{token:room.John})).status,404);
    const db=new DatabaseSync(path.join(directory,'soullink.sqlite'));
    db.prepare('UPDATE cloud_saves SET lease_until=0 WHERE room=?').run(room.id);db.close();
    assert.equal((await call(url,{method:'PUT',token:room.John,data:{...two,baseRevision:12,data:payload.toString('base64')}})).status,423);
    assert.equal((await call(leaseUrl,{method:'POST',token:room.John,data:one})).status,200);
    // Optional end-to-end integration uses the exact Python client shipped in both apps.
    if(process.env.SOULLINK_TEST_PYTHON){
      const cookie=await login('John');
      const otherRoom=await (await call('/api/room',{method:'POST',cookie,data:{}})).json();
      const python=spawn(process.env.SOULLINK_TEST_PYTHON,['desktop/tests/cloud_roundtrip.py'],{env:{...process.env,PYTHONPATH:'desktop'},stdio:['pipe','pipe','pipe']});
      python.stdin.end(JSON.stringify({baseUrl:base,roomId:otherRoom.id,player:'John',token:otherRoom.John,readToken:otherRoom.readToken}));
      let result='';python.stdout.on('data',b=>result+=b);python.stderr.on('data',b=>result+=b);
      const code=await new Promise(resolve=>python.once('exit',resolve));
      assert.equal(code,0,result);console.log(result.trim());
    }
  }finally{await stop();}
});
