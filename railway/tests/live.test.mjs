import {test} from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import {liveRelay} from '../live.mjs';

test('live relay authenticates, parses split frames, follows FPS, isolates players and clears on disconnect',async()=>{
  const authorize=req=>{const role={'Bearer john':'John','Bearer eddie':'Eddie','Bearer read':'read'}[req.headers.authorization];return role?{role}:null;};
  const send=(res,status,data)=>{res.writeHead(status,{'Content-Type':'application/json'});res.end(JSON.stringify(data));};
  const relay=liveRelay({authorize,send});
  const server=http.createServer(async(req,res)=>{await relay.handle(req,res,new URL(req.url,'http://localhost'));});
  await new Promise(r=>server.listen(0,'127.0.0.1',r));
  const base='http://127.0.0.1:'+server.address().port,abort=new AbortController();let upload;
  try{
    assert.equal((await fetch(base+'/api/live?id=room&player=John')).status,401);
    assert.equal((await fetch(base+'/api/live?id=room',{method:'PUT',headers:{Authorization:'Bearer read'}})).status,403);
    assert.equal((await fetch(base+'/api/live?id=room&player=wrong',{headers:{Authorization:'Bearer john'}})).status,400);
    assert.equal((await fetch(base+'/api/live?id=room&publish=1',{headers:{Authorization:'Bearer read'}})).status,403);
    assert.equal((await fetch(base+'/api/live?id=room&publish=1',{headers:{Authorization:'Bearer john'}})).status,200);
    const response=await fetch(base+'/api/live?id=room&player=John',{headers:{Authorization:'Bearer read'},signal:abort.signal});
    const reader=response.body.getReader();
    let pending=Buffer.alloc(0);
    async function frame(){
      while(true){
        if(pending.length>=8){const size=pending.readUInt32BE();if(pending.length>=size+8){const p=pending.subarray(0,size+8);pending=pending.subarray(size+8);return {fps:p.readUInt16BE(4),kind:p.readUInt16BE(6),jpeg:p.subarray(8)};}}
        const chunk=await reader.read();if(chunk.done)throw Error('Unexpected close');pending=Buffer.concat([pending,chunk.value]);
      }
    }
    assert.equal((await frame()).kind,0);
    upload=http.request(base+'/api/live?id=room',{method:'PUT',headers:{Authorization:'Bearer john','Content-Type':'application/x-soullink-frames','Transfer-Encoding':'chunked'}});
    upload.on('error',()=>{});upload.flushHeaders();
    const ready=await new Promise(r=>upload.once('response',r));assert.equal(ready.statusCode,200);ready.resume();
    const jpeg=Buffer.from([255,216,255,217]);
    function packet(fps){const b=Buffer.alloc(12);b.writeUInt32BE(4);b.writeUInt16BE(fps,4);b.writeUInt16BE(1,6);jpeg.copy(b,8);return b;}
    const first=packet(60);upload.write(first.subarray(0,3));upload.write(first.subarray(3,9));upload.write(first.subarray(9));
    let got=await frame();assert.equal(got.fps,60);assert.deepEqual(got.jpeg,jpeg);
    upload.write(Buffer.concat([packet(90),packet(120),packet(0)]));
    assert.equal((await frame()).fps,90);assert.equal((await frame()).fps,120);assert.equal((await frame()).fps,0);
    // Continuous 120 FPS is not throttled to the former preview cadence.
    const start=performance.now();let sent=0,seen=0;
    const producer=setInterval(()=>{upload.write(packet(120));if(++sent===120)clearInterval(producer);},1000/120);
    while(seen<120){const p=await frame();if(p.kind===1){assert.equal(p.fps,120);seen++;}}
    assert(performance.now()-start<1600,'Relay still throttles fast frames');
    const bee=await fetch(base+'/api/live?id=room&player=Eddie',{headers:{Authorization:'Bearer read'},signal:abort.signal});
    const beeReader=bee.body.getReader();assert.equal(Buffer.from((await beeReader.read()).value).readUInt16BE(6),0);await beeReader.cancel();
    upload.end();
    // Rotating the publisher must not flash offline while it reconnects.
    await new Promise(r=>setTimeout(r,100));
    const reconnect=await fetch(base+'/api/live?id=room&player=John',{headers:{Authorization:'Bearer read'},signal:abort.signal});
    const reconnectReader=reconnect.body.getReader();assert.equal(Buffer.from((await reconnectReader.read()).value).readUInt16BE(6),1);await reconnectReader.cancel();
    await reader.cancel();
    const wrong=http.request(base+'/api/live?id=room',{method:'PUT',headers:{Authorization:'Bearer john','Content-Type':'application/x-soullink-frames','Transfer-Encoding':'chunked'}});
    wrong.on('error',()=>{});wrong.flushHeaders();await new Promise(r=>wrong.once('response',res=>{res.resume();r();}));
    const invalid=Buffer.alloc(8);invalid.writeUInt32BE(300001);invalid.writeUInt16BE(1,6);wrong.end(invalid);
    await new Promise(r=>wrong.once('close',r));
  }finally{upload?.destroy();abort.abort();server.closeAllConnections();await new Promise(r=>server.close(r));}
});

test('acknowledged batches are validated atomically and preserve player isolation',async()=>{
  const relay=liveRelay({authorize:req=>({'Bearer john':{role:'John'},'Bearer read':{role:'read'}}[req.headers.authorization]),send:(res,status,data)=>{res.writeHead(status,{'Content-Type':'application/json'});res.end(JSON.stringify(data));}});
  const server=http.createServer(async(req,res)=>{await relay.handle(req,res,new URL(req.url,'http://localhost'));});
  await new Promise(r=>server.listen(0,'127.0.0.1',r));const base='http://127.0.0.1:'+server.address().port;
  const packet=Buffer.from([0,0,0,4,0,120,0,1,255,216,255,217]);
  const post=(data,role='john')=>fetch(base+'/api/live/batch?id=room',{method:'POST',headers:{Authorization:'Bearer '+role,'Content-Type':'application/x-soullink-frames'},body:data});
  try{
    assert.equal((await post(packet,'read')).status,403);
    assert.equal((await post(packet.subarray(0,11))).status,400);
    let response=await post(Buffer.concat(Array(12).fill(packet)));
    assert.equal(response.status,200);assert.deepEqual(await response.json(),{ok:true,accepted:12,player:'John'});
    for(const [player,kind] of [['John',1],['Eddie',0]]){
      const response=await fetch(base+'/api/live?id=room&player='+player,{headers:{Authorization:'Bearer read'}});
      const reader=response.body.getReader();assert.equal(Buffer.from((await reader.read()).value).readUInt16BE(6),kind);await reader.cancel();
    }
    assert.equal((await post(Buffer.concat(Array(65).fill(packet)))).status,400);
  }finally{server.closeAllConnections();await new Promise(r=>server.close(r));}
});
