import test from 'node:test';
import assert from 'node:assert/strict';
import {FramePlayout} from '../../lib/frame-playout.mjs';

for(const [rate,batch,screen,target] of [[64,500,60,120],[60,100,60,120],[120,100,60,120],[120,100,120,120],[30,200,60,120]]){
  test(`playout ${rate} received / ${target} target / ${screen} Hz / ${batch}ms packets`,()=>{
    const p=new FramePlayout();let queue=0,shown=0,nextBatch=0,maxQueue=0;
    for(let now=0;now<15000;now+=1000/screen){
      if(now>=nextBatch){for(let i=0;i<rate*batch/1000;i++){p.receive(nextBatch,target);queue++;}nextBatch+=batch;}
      const take=p.take(now,queue);queue-=take;
      if(take&&now>5000)shown++;
      maxQueue=Math.max(queue,maxQueue);
    }
    assert.ok(shown/10>Math.min(rate,screen)*.85,`displayed ${shown/10}`);
    assert.ok(maxQueue<rate*1.2);
    p.reset();assert.equal(p.take(100000,0),0);
  });
}
