// Gol Informado — gerador de vídeo. Uso: node build.js <pasta-do-projeto> [saida.mp4]
const {chromium}=require('playwright');const http=require('http');const fs=require('fs');const path=require('path');const {spawn,execFileSync}=require('child_process');
const ROOT=path.resolve(__dirname,'..');const proj=path.resolve(process.argv[2]);const out=process.argv[3]||path.join(proj,'video.mp4');
const spec=JSON.parse(fs.readFileSync(path.join(proj,'spec.json')));const fps=spec.fps||30;const W=1080,H=1920;
const cache=path.join(proj,'.cache');fs.mkdirSync(cache,{recursive:true});
const rel=p=>'/'+path.relative(ROOT,p).split(path.sep).join('/');
const ff=(args)=>execFileSync('ffmpeg',['-v','error','-y',...args]);
const COVER=`scale=${W}:${H}:force_original_aspect_ratio=increase,crop=${W}:${H}`;
// 1. pré-processa os clipes (início, velocidade, recorte vertical)
spec.scenes.forEach((s,i)=>{
  if(s.bg.type!=='clip')return;
  const d=path.join(cache,'scene'+i);fs.rmSync(d,{recursive:true,force:true});fs.mkdirSync(d);
  const sp=s.bg.speed||1;
  const cvr=s.bg.cropX!=null?`scale=${W}:${H}:force_original_aspect_ratio=increase,crop=${W}:${H}:(iw-${W})*${s.bg.cropX}:(ih-${H})/2`:COVER;
  const dl=s.bg.delogo?`delogo=x=${s.bg.delogo[0]}:y=${s.bg.delogo[1]}:w=${s.bg.delogo[2]}:h=${s.bg.delogo[3]},`:'';
  ff(['-ss',String(s.bg.start||0),'-t',String(s.dur*sp+0.2),'-i',path.join(proj,s.bg.src),'-an','-vf',`${dl}setpts=PTS/${sp},fps=${fps},${cvr}`,'-q:v','3',path.join(d,'%04d.jpg')]);
  s._n=fs.readdirSync(d).length;
});
// imagens usadas (para detecção de rosto)
const images=new Set();
for(const s of spec.scenes){const b=s.bg;
  if(['photo','card'].includes(b.type))images.add(b.src);
  if(b.type==='split')for(const k of ['left','right'])if(b[k]&&b[k].src)images.add(b[k].src);}
// servidor estático
const MIME={'.html':'text/html','.js':'text/javascript','.json':'application/json','.jpg':'image/jpeg','.jpeg':'image/jpeg','.png':'image/png','.webp':'image/webp','.svg':'image/svg+xml','.woff2':'font/woff2','.bin':'application/octet-stream'};
const srv=http.createServer((q,r)=>{const f=path.join(ROOT,decodeURIComponent(q.url.split('?')[0]));fs.readFile(f,(e,b)=>{if(e){r.writeHead(404);return r.end();}r.writeHead(200,{'Content-Type':MIME[path.extname(f).toLowerCase()]||'application/octet-stream'});r.end(b);});}).listen(0);
const port=srv.address().port,U=p=>`http://127.0.0.1:${port}${p}`;
(async()=>{
  const br=await chromium.launch();
  // 2. detecção de rostos (coordenadas da imagem original)
  const fp=await br.newPage();await fp.goto(U(rel(path.join(__dirname,'faces.html'))));await fp.evaluate(()=>window.ready);
  const faces={},STEP=3;
  for(const im of images)faces[im]=await fp.evaluate(u=>detect(u),U(rel(path.join(proj,im))));
  for(const [i,s] of spec.scenes.entries()){
    if(s.bg.type!=='clip')continue;const fr=[];
    for(let k=0;k<s._n;k+=STEP)fr.push(await fp.evaluate(u=>detect(u),U(rel(path.join(cache,'scene'+i,String(k+1).padStart(4,'0')+'.jpg')))));
    faces['scene'+i]={step:STEP,frames:fr};
  }
  // rostos marcados à mão no spec têm prioridade
  for(const [k,v] of Object.entries(spec.faces||{}))faces[k]=v.map(([x,y,w,h])=>({x,y,w,h}));
  fs.writeFileSync(path.join(cache,'faces.json'),JSON.stringify(faces));
  console.log('rostos:',Object.entries(faces).map(([k,v])=>path.basename(k)+':'+(Array.isArray(v)?v.length:v.frames.filter(f=>f.length).length+'/'+v.frames.length)).join('  '));
  await fp.close();
  // 3. render quadro a quadro
  const pg=await br.newPage({viewport:{width:W,height:H}});
  pg.on('pageerror',e=>console.error('erro na página:',e.message));
  await pg.goto(U(rel(path.join(__dirname,'render.html'))));
  const TD=path.join(__dirname,'transicoes'),trans={};if(fs.existsSync(TD))for(const d of fs.readdirSync(TD))trans[d]=fs.readdirSync(path.join(TD,d)).length;
  const total=await pg.evaluate(([b,s,f,t])=>init(b,s,f,t),[rel(proj),spec,faces,trans]);
  const N=Math.round(total*fps);const vtmp=path.join(cache,'video_noaudio.mp4');
  const enc=spawn('ffmpeg',['-v','error','-y','-f','image2pipe','-framerate',String(fps),'-c:v','mjpeg','-i','-','-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p',vtmp]);
  const only=process.env.FRAMES?process.env.FRAMES.split(',').map(Number):null;
  const t0=Date.now();
  for(let n=0;n<N;n++){
    if(only&&!only.includes(n))continue;
    await pg.evaluate(t=>render(t),n/fps);const buf=await pg.screenshot({type:'jpeg',quality:93});
    if(only){fs.writeFileSync(path.join(cache,`frame_${n}.jpg`),buf);continue;}
    if(!enc.stdin.write(buf))await new Promise(r=>enc.stdin.once('drain',r));
    if(n%90===0)process.stdout.write(`\rquadro ${n}/${N}`);}
  enc.stdin.end();await new Promise(r=>enc.on('close',r));
  if(only){console.log('quadros salvos em .cache');await br.close();srv.close();return;}
  console.log(`\rrender ok: ${N} quadros em ${((Date.now()-t0)/1000).toFixed(0)}s`);
  const ev=await pg.evaluate(()=>events());await br.close();srv.close();
  // 4. áudio: narração + efeitos sonoros sintetizados
  const sfx={pop:'sine=f=700:d=0.09,volume=0.5,afade=t=out:st=0.02:d=0.07',
    hit:'sine=f=70:d=0.35,volume=1.6,afade=t=out:st=0.03:d=0.32',
    whoosh:'anoisesrc=d=0.35:c=pink:a=0.5,highpass=f=500,lowpass=f=4000,afade=t=in:d=0.2,afade=t=out:st=0.2:d=0.15',
    swish:'anoisesrc=d=0.4:c=white:a=0.15,bandpass=f=2500:w=1800,afade=t=in:d=0.15,afade=t=out:st=0.15:d=0.25',
    reveal:'sine=f=1200:d=0.12,volume=0.35,afade=t=out:st=0.02:d=0.1'};
  const sv=spec.sfxVolume??(spec.audio?0.45:1);
  const args=['-f','lavfi','-t',String(total),'-i','anullsrc=r=48000:cl=stereo'];let fc='',n0=2,mixIn='[1]';
  if(spec.audio){args.push('-i',path.join(proj,spec.audio));fc+=`[2]aformat=sample_rates=48000:channel_layouts=stereo[nar];`;mixIn+='[nar]';n0=3;}
  const LIB=path.join(__dirname,'sfx'),VOL={marker:1.8,riser_metallic:1.2,whoosh1:0.7,whoosh2:0.7,whoosh3:0.7,pop1:0.8};
  ev.forEach((e,k)=>{const lf=path.join(LIB,e.k+'.wav');if(fs.existsSync(lf))args.push('-i',lf);else args.push('-f','lavfi','-i',sfx[e.k]);const ms=Math.max(0,Math.round(e.t*1000));fc+=`[${k+n0}]aformat=sample_rates=48000:channel_layouts=stereo,volume=${sv},adelay=${ms}|${ms},volume=${VOL[e.k]??1}[a${k}];`;mixIn+=`[a${k}]`;});
  const nin=1+(spec.audio?1:0)+ev.length;
  fc+=`${mixIn}amix=inputs=${nin}:normalize=0,atrim=0:${total},loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[mix]`;
  ff(['-i',vtmp,...args,'-filter_complex',fc,'-map','0:v','-map','[mix]','-c:v','copy','-c:a','aac','-b:a','192k','-shortest',out]);
  console.log('pronto:',out);
})().catch(e=>{console.error(e);process.exit(1);});
