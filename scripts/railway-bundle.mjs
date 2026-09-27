import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';
const files = Object.fromEntries(['server.mjs','auth.mjs','online.mjs','live.mjs','cloud.mjs','encounters.mjs','login.html'].map(name=>[name,fs.readFileSync('railway/'+name).toString('base64')]));
// Keep the same relative imports in the source tree and deployment bundle.
for(const name of ['server.mjs','encounters.mjs'])files[name]=Buffer.from(fs.readFileSync('railway/'+name,'utf8').replaceAll('../lib/encounters.mjs','./lib/encounters.mjs')).toString('base64');
files['lib/encounters.mjs']=fs.readFileSync('lib/encounters.mjs').toString('base64');
function walk(dir) {
  for (const entry of fs.readdirSync(dir,{withFileTypes:true})) {
    const file=path.join(dir,entry.name);
    if(entry.isDirectory()) walk(file);
    else files[path.relative('railway-dist',file).replaceAll('\\','/')]=fs.readFileSync(file).toString('base64');
  }
}
walk('railway-dist/public');
const encoded=zlib.gzipSync(Buffer.from(JSON.stringify(files))).toString('base64');
const variables={};
const chunks=Math.ceil(encoded.length/16000);
for(let i=0;i<Math.max(chunks,15);i++) variables['SOULLINK_BUNDLE_'+String(i).padStart(3,'0')]=encoded.slice(i*16000,(i+1)*16000);
process.stdout.write(JSON.stringify(variables));
