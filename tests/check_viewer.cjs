// Offline smoke tests: both real generated viewers, canvas coordinates and controls.
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
for(const kind of ['direct','single_face','bat']){
 const html=fs.readFileSync(path.join(__dirname,`../outputs/${kind}_3d.html`),'utf8');
 const script=html.match(/<script>([\s\S]*?)<\/script>/)[1];
 if(/__DATA__|__META__|__AUDIT__/.test(script))throw Error('Unsubstituted data');
 let draws=0,labels=0,nextFrame;
 const ctx=new Proxy({},{get(_,key){return(...args)=>{for(const a of args)if(typeof a==='number'&&!Number.isFinite(a))throw Error('Nonfinite canvas');if(key==='lineTo')draws++;if(key==='fillText')labels++;};},set(){return true;}});
 const elements=new Map();
 function element(id){if(!elements.has(id))elements.set(id,{value:id==='speed'?'1':0,checked:['membranes','structure','cover'].includes(id),width:980,height:640,style:{},parentElement:{style:{}},appendChild(){},getContext(){return ctx;}});return elements.get(id);}
 const sandbox={document:{getElementById:element,createElement(){return{}}},window:{},Math,console,requestAnimationFrame(fn){nextFrame=fn;}};
 vm.runInNewContext(script,sandbox,{timeout:5000});nextFrame(100);nextFrame(200);
 if(draws<30)throw Error('No drawing');
 if(labels!==0)throw Error('Image text should be off by default');
 if(kind==='direct')vm.runInNewContext("if(META.covers.length!==6)throw Error('Missing bat cover'); if(META.boxes.some(b=>b.name==='R/motor'))throw Error('Large body motor remains'); if(!DATA[0].parts.some(p=>p.name==='body_pulley'))throw Error('Remote drive missing')",sandbox);
 if(kind==='bat')vm.runInNewContext("if(!BAT||META.costume.length<20)throw Error('Missing costume');if(elById('structure').checked)throw Error('Drive should start hidden');",sandbox);
 element('labels').checked=true;element('labels').onchange();if(!labels)throw Error('Label toggle failed');element('labels').checked=false;element('labels').onchange();
 element('cover').checked=false;element('cover').onchange();element('cover').checked=true;element('cover').onchange();
 vm.runInNewContext(`(()=>{
  if(DATA[0].gears.length!==${kind!=='compact'?2:6})throw Error('Gear count');
  for(const fr of [DATA[0],DATA[54]]){
   const panels=previewPanels(fr,META.panel_style,META.panel_pitch_deg),ribs=previewRibs(fr,META.panel_style,META.panel_pitch_deg);
   const parts=Object.fromEntries(fr.parts.map(p=>[p.name,p]));
   for(const[n,q]of Object.entries(panels))for(let i=0;i<4;i++)for(let k=0;k<3;k++)if(Math.abs(q[i][k]-fr.panels[n][i][k])>.001)throw Error('Panel mismatch');
   for(const[n,r]of Object.entries(ribs))for(const key of ['p','q'])for(let k=0;k<3;k++)if(Math.abs(r[key][k]-parts[n][key][k])>.001)throw Error('Rib mismatch');
  }
 })()`,sandbox);
 element('panel-shape').value='rectangular';element('panel-shape').onchange();element('panel-pitch').value=25;element('panel-pitch').oninput();
 if(!/Appearance preview|Appearance study/.test(element('preview-note').textContent))throw Error('Missing preview warning');
 element('reset-panels').onclick();element('front').onclick();element('scrub').oninput({target:{value:'54'}});element('cv').onwheel({preventDefault(){},deltaY:1});
 if(!element('status').textContent.includes('Nominal layout: '+(kind==='single_face'?'FAIL':'PASS'))||!element('status').textContent.includes('unverified'))throw Error('Incorrect status');
 element('mechanism').value='inner';element('mechanism').onchange();
 vm.runInNewContext(`(()=>{const g=viewGeometry(DATA[0],META.panel_style,META.panel_pitch_deg);if(g.parts.length!==${kind!=='compact'?10:8}||g.gears.length||Object.keys(g.panels).join()!=='R/inner_panel')throw Error('Isolation failed');})()`,sandbox);
 if(!element('hud').innerHTML.includes('No elbow')||element('status').style.display!=='none')throw Error('Isolated HUD');
 element('mechanism').value='full';element('mechanism').onchange();
 console.log(kind+': rendering, solved panel/rib agreement, controls and shoulder isolation PASS');
}
// Exercise every planar pose and the explanatory toggles offline.
{
 const html=fs.readFileSync(path.join(__dirname,'../outputs/direct_2d.html'),'utf8');
 const script=html.match(/<script>([\s\S]*?)<\/script>/)[1];
 const elements=new Map();
 function element(id){if(!elements.has(id))elements.set(id,{value:id==='loop'?'all':'0',checked:true,setAttribute(){}});return elements.get(id);}
 let next;
 const sandbox={document:{getElementById:element},Math,requestAnimationFrame(fn){next=fn;}};
 vm.runInNewContext(script,sandbox);next(0);next(100);
 vm.runInNewContext('for(let i=0;i<POSES.length;i++){frame=i;draw();}',sandbox);
 if(!element('full').innerHTML.includes('data-wingtip-path'))throw Error('Missing wingtip path');
 if(element('detail').innerHTML.includes('data-wingtip-path'))throw Error('Path should only appear in full view');
 element('trace').checked=false;element('trace').onchange();
 if(element('full').innerHTML.includes('data-wingtip-path'))throw Error('Path toggle failed');
 vm.runInNewContext("if(tipPath.split(' ').length!==POSES.length+1)throw Error('Incomplete path');",sandbox);
 for(const id of ['targets','triangles']){element(id).checked=false;element(id).onchange();}
 for(const value of ['shoulder','elbow','all']){element('loop').value=value;element('loop').onchange();}
 if(/NaN|Infinity|undefined/.test(element('full').innerHTML)||!element('full').innerHTML.includes('<line'))throw Error('Invalid planar drawing');
 console.log('2d: all solved poses and explanatory controls PASS');
}
