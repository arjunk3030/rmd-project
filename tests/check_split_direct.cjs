const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync('outputs/split_direct_3d.html','utf8');
const script=html.match(/<script>([\s\S]*?)<\/script>/)[1];
const elements=new Map();let polygons=0;
const ctx=new Proxy({}, {get(_,key){return(...args)=>{for(const a of args)if(typeof a==='number')assert(Number.isFinite(a));if(key==='fill')polygons++;};},set(){return true;}});
function element(id){if(!elements.has(id))elements.set(id,{value:id==='speed'?'1':0,checked:['structure','hardware'].includes(id),width:980,height:640,style:{},parentElement:{style:{}},appendChild(){},getContext(){return ctx;}});return elements.get(id);}
const sandbox={document:{getElementById:element,createElement(){return{};},body:{classList:{add(){}}}},window:{},Math,console,requestAnimationFrame(){}};
vm.runInNewContext(script,sandbox);vm.runInNewContext('for(let i=0;i<DATA.length;i++){frame=i;draw();if(DATA[i].gears.length)throw Error("Unexpected gears")}',sandbox);
assert(polygons>10000);assert(element('status').textContent.includes('unverified'));
const parse=file=>JSON.parse(fs.readFileSync(file,'utf8').match(/const DATA=(.*),META=/)[1]);
const x=parse('outputs/split_direct_3d.html'),old=parse('outputs/direct_3d.html');
for(let i=0;i<x.length;i++){
 for(const key of ['theta_deg','alpha_deg','F_deg','mu1_deg','mu2_deg'])assert.equal(x[i][key],old[i][key]);
 for(const p of x[i].parts){const previous=old[i].parts.find(q=>q.name===p.name);for(const end of ['p','q'])assert.deepEqual(p[end].slice(1),previous[end].slice(1));}
}
const report=JSON.parse(fs.readFileSync('outputs/split_direct/clearance.json'));assert(report.D_screw_to_AB_axial_gap_mm>0);assert.equal(report.inner_D_trial.status,'FAIL');
console.log('Split-face: all poses render; one wing, no gears; pivot motion preserved; inside-D conflict recorded.');
