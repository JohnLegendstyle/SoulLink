import {test} from 'node:test';
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {scryptSync} from 'node:crypto';
import {mkdtempSync} from 'node:fs';
import {tmpdir} from 'node:os';
import path from 'node:path';

test('private login, pairing, retired video endpoints, teams and persistence',async()=>{
  const directory=mkdtempSync(path.join(tmpdir(),'soullink-online-test-'));
  const password='test-only-focus',salt='test-salt';
  const env={...process.env,DATA_DIR:directory,PUBLIC_DIR:path.resolve('railway-dist/public'),PORT:'0',SOULLINK_LOCAL_TEST:'1',SOULLINK_PASSWORD_HASH:salt+':'+scryptSync(password,salt,32).toString('hex')};
  let child,base;
  async function start(){
    child=spawn(process.execPath,['railway/server.mjs'],{env,stdio:['ignore','pipe','pipe']});
    let output='';child.stderr.on('data',b=>output+=b);
    await new Promise((resolve,reject)=>{const timeout=setTimeout(()=>reject(Error(output||'Server timeout')),5000);child.stdout.on('data',b=>{const match=String(b).match(/SoulLink ready (\d+)/);if(match){base='http://127.0.0.1:'+match[1];clearTimeout(timeout);resolve();}});child.once('exit',code=>{clearTimeout(timeout);reject(Error('Server exited '+code+output));});});
  }
  async function stop(){if(child.exitCode!==null)return;await new Promise(resolve=>{child.once('exit',resolve);child.kill('SIGTERM');});}
  async function request(route,{method='GET',data,cookie,token,type}={}){
    const headers={};if(cookie)headers.Cookie=cookie;if(token)headers.Authorization='Bearer '+token;
    let payload;if(data!==undefined){headers['Content-Type']=type||'application/json';payload=type?data:JSON.stringify(data);}
    return fetch(base+route,{method,headers,body:payload});
  }
  async function login(username){const r=await request('/api/login',{method:'POST',data:{username,password}});assert.equal(r.status,200);assert.match(r.headers.get('set-cookie'),/HttpOnly/);return r.headers.get('set-cookie').split(';')[0];}
  try{
    await start();
    assert.match(await (await request('/')).text(),/Bitte anmelden/);
    assert.equal((await request('/api/account')).status,401);
    assert.equal((await request('/api/login',{method:'POST',data:{username:'John',password:'wrong'}})).status,401);
    assert.equal((await request('/api/login',{method:'POST',data:{username:'Intruder',password}})).status,401);
    let john=await login('John'),eddie=await login('Eddie');
    const room=await (await request('/api/room',{method:'POST',cookie:john,data:{}})).json();
    assert.ok(room.John);assert.equal(room.Eddie,undefined);
    const bee=(await (await request('/api/account',{cookie:eddie})).json()).access;
    assert.equal(bee.id,room.id);assert.ok(bee.Eddie);assert.equal(bee.John,undefined);
    const grant=await (await request('/api/pair',{method:'POST',data:{}})).json();
    assert.equal((await request('/api/pair?id='+grant.id,{token:room.readToken})).status,401);
    assert.equal((await request('/api/pair/approve',{method:'POST',token:room.John,data:{deviceId:grant.id,roomId:room.id,readToken:room.readToken}})).status,401);
    assert.equal((await request('/api/pair/approve',{method:'POST',cookie:eddie,token:room.John,data:{deviceId:grant.id,roomId:room.id,readToken:room.readToken}})).status,401);
    const approval=await request('/api/pair/approve',{method:'POST',cookie:john,token:room.John,data:{deviceId:grant.id,roomId:room.id,readToken:room.readToken}});assert.equal(approval.status,200);
    const paired=await (await request('/api/pair?id='+grant.id,{token:grant.secret})).json();assert.equal(paired.access.token,room.John);assert.equal(paired.status,'approved');
    assert.equal((await request('/api/pair/approve',{method:'POST',cookie:john,token:room.John,data:{deviceId:grant.id,roomId:room.id,readToken:room.readToken}})).status,409);
    for(const endpoint of ['/api/frame','/api/live','/api/live/batch']){
      for(const method of ['GET','PUT','POST']){
        const reply=await request(endpoint+'?id='+room.id,{method,token:room.John});
        assert.equal(reply.status,410);assert.equal((await reply.json()).videoDisabled,true);
      }
    }
    assert.equal((await request('/api/sync',{method:'POST',token:room.John,data:{roomId:room.id,heartbeat:true}})).status,200);
    const pokemon=uid=>({uid,species:25,nickname:'Test',level:5,hp:20,maxHp:20});
    for(const [role,token,uid] of [['John',room.John,'test-optimus'],['Eddie',bee.Eddie,'test-bee']]){
      assert.equal((await request('/api/sync',{method:'POST',token,data:{roomId:room.id,sessionId:'test',sequence:0,party:[pokemon(uid)],owned:[pokemon(uid)],fainted:[]}})).status,200);
    }
    const dead={...pokemon('test-optimus'),hp:0};
    await request('/api/sync',{method:'POST',token:room.John,data:{roomId:room.id,sessionId:'test',sequence:1,party:[dead],owned:[dead],fainted:[dead.uid]}});
    const position={mapId:33,x:704,y:422,direction:1,capturedAt:Date.now()};
    const heartbeat=await (await request('/api/sync',{method:'POST',token:bee.Eddie,data:{roomId:room.id,heartbeat:true,position}})).json();
    assert.deepEqual(heartbeat.blocked,['test-bee']);assert.equal(heartbeat.partnerOnline,true);
    assert.equal((await request('/api/sync',{method:'POST',token:bee.Eddie,data:{roomId:room.id,heartbeat:true,position:{...position,direction:9}}})).status,400);
    assert.equal((await request('/api/room',{method:'PATCH',cookie:john,token:room.readToken,data:{id:room.id,pair:0,name:'Test-Paar'}})).status,200);
    const state=(await (await request('/api/room?id='+room.id,{cookie:john,token:room.readToken})).json()).state;
    assert.equal(state.names['0'],'Test-Paar');assert.deepEqual(state.John.dead,['test-optimus']);assert.deepEqual(state.Eddie.position.mapId,33);
    // Location metadata enriches existing identities without reordering pairs.
    const caught={...pokemon('test-optimus'),metLocation:177,originGame:8,isEgg:false,eggLocation:0};
    await request('/api/sync',{method:'POST',token:room.John,data:{roomId:room.id,sessionId:'test',sequence:2,party:[caught],owned:[caught],fainted:[]}});
    // Old apps omit metadata: do not erase the newly learned location.
    await request('/api/sync',{method:'POST',token:room.John,data:{roomId:room.id,sessionId:'test',sequence:3,party:[pokemon('test-optimus')],owned:[],fainted:[]}});
    // A catch sent directly to a full PC party is paired with an explicit miss
    // placeholder, so the next successful catches cannot shift out of line.
    const boxed={...pokemon('john-boxed'),level:null,hp:null,maxHp:null,metLocation:179,originGame:8,isEgg:false,eggLocation:0};
    await request('/api/sync',{method:'POST',token:room.John,data:{roomId:room.id,sessionId:'test',sequence:4,party:[caught],owned:[caught,boxed],fainted:[]}});
    assert.equal((await request('/api/encounters',{method:'PATCH',cookie:eddie,token:bee.Eddie,data:{id:room.id,location:179,status:'missed'}})).status,200);
    const failedHeartbeat=await (await request('/api/sync',{method:'POST',token:room.John,data:{roomId:room.id,heartbeat:true}})).json();
    assert.ok(failedHeartbeat.blocked.includes('john-boxed'));
    const mark={method:'PATCH',cookie:john,token:room.John,data:{id:room.id,location:178,status:'missed'}};
    assert.equal((await request('/api/encounters',{...mark,token:room.readToken})).status,403);
    assert.equal((await request('/api/encounters',{...mark,cookie:eddie})).status,403);
    assert.equal((await request('/api/encounters',{...mark,data:{...mark.data,location:99999}})).status,400);
    assert.equal((await request('/api/encounters',mark)).status,200);
    await request('/api/sync',{method:'POST',token:room.John,data:{roomId:room.id,sessionId:'test',sequence:5,party:[],owned:[],fainted:[]}});
    const mapped=(await (await request('/api/room?id='+room.id,{cookie:john,token:room.readToken})).json()).state;
    assert.equal(mapped.John.seen[0].metLocation,177);assert.equal(mapped.John.encounters[178].status,'missed');assert.equal(mapped.Eddie.encounters[179].status,'missed');assert.equal(mapped.Eddie.seen[1].missed,true);
    await stop();await start();john=await login('John');eddie=await login('Eddie');
    assert.equal((await (await request('/api/account',{cookie:eddie})).json()).access.id,room.id);
    assert.equal((await (await request('/api/account',{cookie:john})).json()).access.John,room.John);
    const persisted=(await (await request('/api/room?id='+room.id,{cookie:john,token:room.readToken})).json()).state;
    assert.equal(persisted.John.encounters[178].status,'missed');assert.equal(persisted.John.seen[0].metLocation,177);
    assert.equal((await request('/api/encounters',{...mark,cookie:john,data:{...mark.data,status:'auto'}})).status,200);
    await request('/api/logout',{method:'POST',cookie:john});assert.equal((await request('/api/account',{cookie:john})).status,401);
  }finally{await stop();}
});
