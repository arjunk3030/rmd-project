const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync('outputs/offset_experiment_3d.html','utf8');
const script=html.match(/<script>([\s\S]*?)<\/script>/)[1];
const elements=new Map();let draws=0;
const ctx=new Proxy({}, {get(_,key){return(...args)=>{for(const a of args)if(typeof a==='number')assert(Number.isFinite(a));if(key==='fill')draws++;};},set(){return true;}});
function element(id){if(!elements.has(id))elements.set(id,{value:id==='speed'?'1':0,checked:['structure','hardware'].includes(id),width:980,height:640,style:{},parentElement:{style:{}},appendChild(){},getContext(){return ctx;}});return elements.get(id);}
const sandbox={document:{getElementById:element,createElement(){return{};},body:{classList:{add(){}}}},window:{},Math,console,requestAnimationFrame(){}};
vm.runInNewContext(script,sandbox);
vm.runInNewContext('for(let i=0;i<DATA.length;i++){frame=i;draw();}',sandbox);
assert(draws>10000);assert(element('status').textContent.includes('FAIL'));
element('collision').onclick();assert.equal(element('scrub').value,21);
const parse=file=>JSON.parse(fs.readFileSync(file,'utf8').match(/const DATA=(.*),META=/)[1]);
assert.deepEqual(parse('outputs/offset_experiment_3d.html'),parse('outputs/mockup_3d.html'));
const report=JSON.parse(fs.readFileSync('outputs/offset_experiment/clearance.json'));assert.equal(report.status,'FAIL');assert(report.results.some(x=>x.bridge_leg&&x.intersects));assert(report.results.some(x=>x.front_section&&x.intersects));
console.log('Offset experiment: all poses render, detected collisions reported, navigation works.');
