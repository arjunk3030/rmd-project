// Approximate reference objects, independent of the mechanism and its checks.
function drawScaleReferences(poly,box){
 // A generic upright phone: 150 × 72 × 8 mm.
 const phone={center:[0,330,-80],size:[8,72,150]};
 box(phone,'#454d58');
 poly([[-4.1,297,-148],[-4.1,363,-148],[-4.1,363,-12],[-4.1,297,-12]],'#1d2734');
 poly([[-4.2,321,-19],[-4.2,339,-19],[-4.2,339,-17],[-4.2,321,-17]],'#738293');
 // Stylized adult hand: approximately 180 mm long and 82 mm across.
 const y=-330,z=-155,x=0,outline=[[-24,0],[-26,50],[-35,60],[-49,84],[-47,95],[-41,98],[-24,76],[-26,137],[-24,150],[-19,154],[-14,149],[-13,119],[-13,168],[-10,174],[-5,174],[-2,167],[-1,121],[1,175],[5,180],[9,176],[10,121],[13,165],[17,170],[21,166],[20,118],[24,145],[28,148],[32,144],[31,91],[28,66],[24,49],[23,0]];
 const front=outline.map(([a,b])=>[x-8,y+a,z+b]),back=outline.map(([a,b])=>[x+8,y+a,z+b]);
 poly(front,'#d6ad92');poly(back,'#bc927b');
 for(let i=0;i<front.length;i++){let j=(i+1)%front.length;poly([front[i],front[j],back[j],back[i]],'#c39b83');}
}
