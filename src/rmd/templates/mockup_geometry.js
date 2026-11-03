// Printed solids and illustrative axial hardware, using the saved joint centers.
function drawMockup(fr,cfg,poly,hardware,highlight=false,structure=true){
 const parts=Object.fromEntries(fr.parts.map(p=>[p.name,p]));
 const t=cfg.plate_thickness_mm,r=cfg.bearing_outer_diameter_mm/2+cfg.boss_wall_mm;
 function hull(points){
  const sorted=points.slice().sort((a,b)=>a[1]-b[1]||a[2]-b[2]);
  const cross=(a,b,c)=>(b[1]-a[1])*(c[2]-a[2])-(b[2]-a[2])*(c[1]-a[1]);
  function half(ps){const h=[];for(const p of ps){while(h.length>1&&cross(h.at(-2),h.at(-1),p)<=0)h.pop();h.push(p);}return h;}
  return half(sorted).slice(0,-1).concat(half(sorted.reverse()).slice(0,-1));
 }
 function prism(points,thickness,color,bores=[]){
  // The printed outline includes rounded bearing seats, with actual open bores.
  const circle=(c,r)=>Array.from({length:24},(_,i)=>[c[0],c[1]+r*Math.cos(i*Math.PI/12),c[2]+r*Math.sin(i*Math.PI/12)]);
  const outline=bores.length?hull([...points,...bores.flatMap(c=>circle(c,r))]):points;
  const shift=(ps,dx)=>ps.map(p=>[p[0]+dx,p[1],p[2]]);
  const lo=shift(outline,-thickness/2),hi=shift(outline,thickness/2);
  const holes=bores.map(c=>circle(c,c[3]===undefined?cfg.bearing_outer_diameter_mm/2:c[3]));
  poly(lo,color,holes.map(h=>shift(h,-thickness/2)));poly(hi,color,holes.map(h=>shift(h,thickness/2)));
  for(const boundary of [outline,...holes]){const a=shift(boundary,-thickness/2),b=shift(boundary,thickness/2);for(let i=0;i<a.length;i++){const j=(i+1)%a.length;poly([a[i],a[j],b[j],b[i]],color);}}
 }
 function ring(center,outer,inner,width,color,n=12){
  const points=(x,r)=>Array.from({length:n},(_,i)=>[x,center[1]+r*Math.cos(i*2*Math.PI/n),center[2]+r*Math.sin(i*2*Math.PI/n)]);
  const a=points(center[0]-width/2,outer),b=points(center[0]+width/2,outer),c=points(center[0]-width/2,inner),d=points(center[0]+width/2,inner);
  for(let i=0;i<n;i++){const j=(i+1)%n;for(const q of [[a[i],a[j],c[j],c[i]],[b[i],b[j],d[j],d[i]],[a[i],a[j],b[j],b[i]],[c[i],c[j],d[j],d[i]]])poly(q,color);}
 }
 function bar(a,b,color,bores=[]){
  const length=Math.hypot(b[1]-a[1],b[2]-a[2]),dy=-(b[2]-a[2])/length*cfg.link_width_mm/2,dz=(b[1]-a[1])/length*cfg.link_width_mm/2;
  prism([[a[0],a[1]+dy,a[2]+dz],[b[0],b[1]+dy,b[2]+dz],[b[0],b[1]-dy,b[2]-dz],[a[0],a[1]-dy,a[2]-dz]],t,color,bores);
 }
 for(const side of ['R']){
  const p=(name,end)=>parts[side+'/'+name][end];
  const O=p('crank1','p'),A=p('crank1','q'),D=p('crank2_direct','q'),S=p('rocker1','p'),B=p('rocker1','q'),E=p('inner_spar','q'),Q=p('elbow_horn','q'),T=p('outer_spar','q');
  const split=!!cfg.split_face;
  if(split){
   const OD=p('crank2_direct','p');
   bar(O,A,'#438bff',[[...O,cfg.screw_diameter_mm/2],A]);
   bar(OD,D,'#438bff',[[...OD,cfg.screw_diameter_mm/2],D]);
   ring([(O[0]+OD[0])/2,O[1],O[2]],cfg.screw_diameter_mm/2,0,Math.abs(OD[0]-O[0])+4,'#8795a3',12);
   if(structure)ring([21.5,O[1],O[2]],7,0,5,'#687687',16);
  }else prism([O,A,D],t,'#438bff',[O,A,D]);
  prism([S,B,E],t,'#ffe23b',[S,B,E]);
  const ap=p('coupler1','p'),bp=p('coupler1','q'),couplerColor=highlight?'#ff4f58':'#438bff';
  if(cfg.coupler_bridge_mm){
   const len=Math.hypot(bp[1]-ap[1],bp[2]-ap[2]),u=[0,(bp[1]-ap[1])/len,(bp[2]-ap[2])/len],v=[0,-u[2],u[1]],step=9.5;
   const move=(p,d)=>p.map((x,i)=>x+u[i]*d),as=move(ap,step),bs=move(bp,-step);
   const back=p=>[p[0]-cfg.coupler_bridge_mm,p[1],p[2]];
   bar(ap,as,couplerColor,[ap]);bar(bs,bp,couplerColor,[bp]);bar(back(as),back(bs),couplerColor);
   function leg(c){const side=4,lo=c[0]-cfg.coupler_bridge_mm,hi=c[0],corners=[];
    for(const x of [lo,hi])for(const y of [-side,side])for(const z of [-side,side])corners.push([x,c[1]+y*u[1]+z*v[1],c[2]+y*u[2]+z*v[2]]);
    for(const ids of [[0,1,3,2],[4,5,7,6],[0,1,5,4],[2,3,7,6],[0,2,6,4],[1,3,7,5]])poly(ids.map(i=>corners[i]),couplerColor);
   }leg(as);leg(bs);
  }else bar(ap,bp,couplerColor,[ap,bp]);
  bar(p('rod2_direct','p'),p('rod2_direct','q'),'#438bff',[p('rod2_direct','p'),p('rod2_direct','q')]);
  const outerE=[Q[0],E[1],E[2]],outerT=[Q[0],T[1],T[2]];
  bar(outerE,Q,'#ffe23b',[outerE,Q]);bar(outerE,outerT,'#ffe23b',[outerE]);
  if(structure){for(const x of (cfg.support_planes_x_mm||[cfg.support_plane_x_mm])){const oy=(O[1]+S[1])/2,oz=(O[2]+S[2])/2;prism([[x,oy-18,oz-29],[x,oy+18,oz-29],[x,oy+18,oz+29],[x,oy-18,oz+29]],4,'#536a7c',[[x,O[1],O[2]],[x,S[1],S[2]]]);if(split){ring([x,O[1],O[2]],5,1.5,3,'#aebdca');ring([x,S[1],S[2]],5,1.5,3,'#aebdca');}}}
  const joints=[['O',[O], '#438bff'],['A',[A,p('coupler1','p')],'#438bff'],['D',[D,p('rod2_direct','p')],'#438bff'],['S',[S],'#ffe23b'],['B',[B,p('coupler1','q')],'#ffe23b'],['E',[E,outerE],'#ffe23b'],['Q',[Q,p('rod2_direct','q')],'#438bff']];
  for(const[name,centers,color]of joints){
   if(split&&name==='O')continue;
   // Seats belong to the printed body; do not overlay extra plastic rings.
   if(!hardware&&!(highlight&&name==='D'))continue;
   const c=centers[0],xs=centers.map(p=>p[0]),lo=Math.min(...xs)-t/2-1,hi=Math.max(...xs)+t/2+1;
   for(const seat of centers)ring(seat,cfg.bearing_outer_diameter_mm/2,cfg.bearing_bore_mm/2,cfg.bearing_width_mm,'#aebdca');
   // A continuous screw axis, with hex head and nut outside the link stack.
   ring([(lo+hi)/2,c[1],c[2]],cfg.screw_diameter_mm/2,0,hi-lo,'#8795a3',8);
   ring([lo-1,c[1],c[2]],cfg.head_diameter_mm/2,0,2,'#8795a3',6);
   ring([hi+cfg.nut_thickness_mm/2,c[1],c[2]],cfg.nut_across_flats_mm/Math.sqrt(3),cfg.screw_diameter_mm/2,cfg.nut_thickness_mm,'#8795a3',6);
  }
 }
}
