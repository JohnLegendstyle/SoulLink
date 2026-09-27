// Pace real frames at the measured arrival rate, not the emulator's FPS target.
export class FramePlayout {
  constructor(){this.reset();}
  reset(){this.rate=60;this.start=null;this.count=0;this.next=null;this.last=null;this.gap=100;}
  receive(now,target){
    if(this.start===null){this.start=now;this.rate=target||60;}
    else if(now-this.start>=1000){
      this.rate=Math.max(1,Math.min(1000,this.count*1000/(now-this.start)));
      this.start=now;this.count=0;
    }
    this.count++;
    if(this.last!==null&&now-this.last>10)this.gap=Math.min(500,Math.max(40,now-this.last));
    this.last=now;
  }
  take(now,available){
    if(!available){this.next=null;return 0;}
    if(this.next===null)this.next=now+Math.min(350,Math.max(100,this.gap));
    if(now<this.next)return 0;
    const step=1000/this.rate;
    const count=Math.min(available,Math.floor((now-this.next)/step)+1);
    this.next+=count*step;
    // Never catch up an old paused timeline by dropping an entire new batch.
    if(this.next<now-100)this.next=now+step;
    return count;
  }
}
