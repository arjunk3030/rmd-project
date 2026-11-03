const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync('outputs/mockup_3d.html','utf8');
const script=html.match(/<script>([\s\S]*?)<\/script>/)[1];
const elements=new Map();let polygons=0;
const ctx=new Proxy({}, {get(_,key){return(...args)=>{for(const a of args)if(typeof a==='number')assert(Number.isFinite(a));if(key==='fill')polygons++;};},set(){return true;}});
function element(id){if(!elements.has(id))elements.set(id,{value:id==='speed'?'1':0,checked:['structure','hardware'].includes(id),width:980,height:640,style:{},parentElement:{style:{}},appendChild(){},getContext(){return ctx;}});return elements.get(id);}
const sandbox={document:{getElementById:element,createElement(){return{};},body:{classList:{add(){}}}},window:{},Math,console,requestAnimationFrame(){}};
vm.runInNewContext(script,sandbox);
vm.runInNewContext(`for(let i=0;i<DATA.length;i++){frame=i;draw();if(Object.keys(DATA[i].panels).length)throw Error('Cloth retained');}`,sandbox);
assert(polygons>10000);assert(element('status').textContent.includes('unverified'));
let count=0;vm.runInNewContext('frame=0;draw()',sandbox);const before=polygons;
element('hardware').checked=false;element('hardware').onchange();const without=polygons-before;
element('hardware').checked=true;element('hardware').onchange();assert(polygons-before-without>without);
const parse=file=>JSON.parse(fs.readFileSync(file,'utf8').match(/const DATA=(.*),META=/)[1]);
const a=parse('outputs/mockup_3d.html'),b=parse('outputs/single_face_3d.html');
for(let i=0;i<a.length;i++){assert.deepEqual(a[i].parts.filter(p=>!p.name.endsWith('_shaft')),b[i].parts.filter(p=>p.name.startsWith('R/')&&!p.name.endsWith('_shaft')));assert.equal(a[i].gears.length,0);}
element('collision').onclick();assert.equal(element('scrub').value,57);assert(element('highlight').checked);
for(let i=0;i<a.length;i++)for(const key of ['theta_deg','alpha_deg','F_deg','mu1_deg','mu2_deg'])assert.deepEqual(a[i][key],b[i][key]);
console.log('Mock-up: all poses render; no cloth; hardware toggle works; saved motion preserved.');
