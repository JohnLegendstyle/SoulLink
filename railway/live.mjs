// Bounded, authenticated, video-only frame relay. No credentials in URLs.
// Frame: uint32 JPEG length, uint16 configured FPS (0 = unlimited), uint16 kind.
// Kind 1 = JPEG, 0 = offline, 2 = keepalive. All integers are big-endian.
export function liveRelay({authorize,send,onFrame=()=>{}}){
  const channels=new Map();let viewers=0,publishers=0;
  const control=kind=>{const b=Buffer.alloc(8);b.writeUInt16BE(kind,6);return b;};
  function channel(key){
    let c=channels.get(key);
    if(!c){if(channels.size>=100)return null;c={viewers:new Set(),latest:null,at:Date.now(),publisher:null};channels.set(key,c);}
    return c;
  }
  function write(view,packet){
    if(view.res.destroyed)return;
    if(view.blocked){view.pending=packet;return;}
    view.blocked=!view.res.write(packet);
  }
  function publish(key,jpeg,fps=4,notify=true){
    const c=channel(key);if(!c)return;
    const header=Buffer.alloc(8);header.writeUInt32BE(jpeg.length);header.writeUInt16BE(fps,4);header.writeUInt16BE(1,6);
    const packet=Buffer.concat([header,jpeg]);c.latest=packet;c.at=Date.now();
    if(notify)for(const v of c.viewers)write(v,packet);
    onFrame(key,jpeg);
  }
  function clear(key){const c=channels.get(key);if(!c)return;c.latest=null;for(const v of c.viewers)write(v,control(0));}
  setInterval(()=>{
    for(const [key,c] of channels){
      if(c.latest&&Date.now()-c.at>6000)clear(key);
      for(const v of c.viewers){
        if(v.res.writableLength>600000||Date.now()-v.started>55000){v.res.end();continue;}
        write(v,control(c.latest?2:0));
      }
      if(!c.publisher&&!c.viewers.size&&Date.now()-c.at>6000)channels.delete(key);
    }
  },1000).unref();
  async function handle(req,res,url){
    if(!['/api/live','/api/live/batch'].includes(url.pathname))return false;
    const id=url.searchParams.get('id'),a=authorize(req,id);
    if(!a){send(res,401,{error:'Privater Zugang erforderlich.'});return true;}
    if(url.pathname==='/api/live/batch'){
      if(req.method!=='POST'){send(res,405,{error:'POST erforderlich.'});return true;}
      if(a.role==='read'){send(res,403,{error:'Nur der Spieler darf senden.'});return true;}
      if(req.headers['content-type']!=='application/x-soullink-frames'){send(res,415,{error:'Frame-Paket erforderlich.'});return true;}
      const key=id+':'+a.role,c=channel(key);
      if(!c){send(res,503,{error:'Übertragung ausgelastet.'});return true;}
      let size=0;const chunks=[];
      for await(const chunk of req){size+=chunk.length;if(size>4000000){send(res,413,{error:'Paket zu groß.'});return true;}chunks.push(chunk);}
      const packet=Buffer.concat(chunks),frames=[];let offset=0;
      while(offset+8<=packet.length){
        const length=packet.readUInt32BE(offset),fps=packet.readUInt16BE(offset+4),kind=packet.readUInt16BE(offset+6);
        if(kind!==1||length<4||length>300000||fps>1000||offset+8+length>packet.length||frames.length>=64){send(res,400,{error:'Ungültiges Frame-Paket.'});return true;}
        const jpeg=packet.subarray(offset+8,offset+8+length);
        if(jpeg[0]!==255||jpeg[1]!==216||jpeg.at(-2)!==255||jpeg.at(-1)!==217){send(res,400,{error:'Ungültiges Bild.'});return true;}
        frames.push({jpeg,fps});offset+=8+length;
      }
      if(offset!==packet.length||!frames.length){send(res,400,{error:'Unvollständiges Frame-Paket.'});return true;}
      // A finite acknowledged request traverses Windows/proxy connections
      // reliably, unlike a permanently half-open chunked upload.
      const now=Date.now();
      if(!c.batchAt||now-c.batchAt>=1000){c.batchAt=now;c.batchBytes=0;c.batchRequests=0;}
      c.batchBytes+=size;c.batchRequests++;
      if(c.batchBytes>50000000||c.batchRequests>30){send(res,429,{error:'Übertragung zu schnell.'});return true;}
      for(const f of frames)publish(key,f.jpeg,f.fps,false);
      // Keep a received batch together: writing its individual JPEGs in a
      // synchronous burst would hit backpressure and discard most frames.
      for(const v of c.viewers)write(v,packet);
      send(res,200,{ok:true,accepted:frames.length,player:a.role});return true;
    }
    if(req.method==='GET'){
      if(url.searchParams.get('publish')==='1'){
        send(res,a.role==='read'?403:200,a.role==='read'?{error:'Nur der Spieler darf senden.'}:{ok:true});return true;
      }
      const role=url.searchParams.get('player');
      if(!['John','Eddie'].includes(role)){send(res,400,{error:'Unbekannter Spieler.'});return true;}
      const c=channel(id+':'+role);
      if(!c||viewers>=32||c.viewers.size>=8){send(res,503,{error:'Zu viele Zuschauer.'});return true;}
      const view={res,blocked:false,pending:null,started:Date.now()};c.viewers.add(view);viewers++;
      res.writeHead(200,{'Content-Type':'application/x-soullink-frames','Cache-Control':'no-store, no-transform','X-Accel-Buffering':'no','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer'});
      res.flushHeaders();req.socket.setNoDelay(true);
      res.on('drain',()=>{view.blocked=false;if(view.pending){const packet=view.pending;view.pending=null;write(view,packet);}});
      res.on('close',()=>{if(c.viewers.delete(view))viewers--;view.pending=null;});
      write(view,c.latest||control(0));return true;
    }
    if(req.method!=='PUT'){send(res,405,{error:'Methode nicht erlaubt.'});return true;}
    if(a.role==='read'){send(res,403,{error:'Nur der Spieler darf senden.'});return true;}
    if(req.headers['content-type']!=='application/x-soullink-frames'){send(res,415,{error:'Frame-Stream erforderlich.'});return true;}
    const key=id+':'+a.role,c=channel(key);
    if(!c||publishers>=8){send(res,503,{error:'Übertragung ausgelastet.'});return true;}
    // Reconnects replace only this player's previous stream, never the partner.
    if(c.publisher)c.publisher.destroy();c.publisher=req;publishers++;
    req.socket.setNoDelay(true);req.setTimeout(15000,()=>req.destroy());
    res.writeHead(200,{'Content-Type':'text/plain','Cache-Control':'no-store','X-Accel-Buffering':'no'});res.flushHeaders();res.write('ready\n');
    const timeout=setTimeout(()=>req.destroy(),55000);timeout.unref();
    let pending=Buffer.alloc(0),budget=50000000,last=Date.now();
    try{
      for await(const chunk of req){
        const now=Date.now();budget=Math.min(50000000,budget+(now-last)*50000)-chunk.length;last=now;
        if(budget<0)throw Error('Rate limit');
        pending=Buffer.concat([pending,chunk]);
        while(pending.length>=8){
          const size=pending.readUInt32BE(0),fps=pending.readUInt16BE(4),kind=pending.readUInt16BE(6);
          if(size>300000||fps>1000||(kind!==1&&kind!==2)||(kind===2&&size!==0)||(kind===1&&size<4))throw Error('Invalid frame');
          if(pending.length<size+8)break;
          if(kind===1){
            const jpeg=pending.subarray(8,8+size);
            if(jpeg[0]!==255||jpeg[1]!==216||jpeg.at(-2)!==255||jpeg.at(-1)!==217)throw Error('Invalid JPEG');
            publish(key,jpeg,fps);
          }
          pending=pending.subarray(size+8);
        }
      }
    }catch{req.destroy();}
    finally{
      clearTimeout(timeout);publishers--;
      // Keep the last image during the normal 50-second publisher reconnect.
      // The six-second freshness timeout, not a socket rotation, marks offline.
      if(c.publisher===req)c.publisher=null;
      if(!res.destroyed)res.end();
    }
    return true;
  }
  return {handle,publish,clear};
}
