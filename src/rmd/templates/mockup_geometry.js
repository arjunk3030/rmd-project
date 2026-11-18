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
 function prism(points,thickness,color,bores=[],cutouts=[]){
  // The printed outline includes rounded bearing seats, with actual open bores.
  const circle=(c,r)=>Array.from({length:24},(_,i)=>[c[0],c[1]+r*Math.cos(i*Math.PI/12),c[2]+r*Math.sin(i*Math.PI/12)]);
  const outline=bores.length?hull([...points,...bores.flatMap(c=>circle(c,r))]):points;
  const shift=(ps,dx)=>ps.map(p=>[p[0]+dx,p[1],p[2]]);
  const lo=shift(outline,-thickness/2),hi=shift(outline,thickness/2);
  const holes=bores.map(c=>circle(c,c[3]===undefined?cfg.bearing_outer_diameter_mm/2:c[3])).concat(cutouts);
  poly(lo,color,holes.map(h=>shift(h,-thickness/2)));poly(hi,color,holes.map(h=>shift(h,thickness/2)));
  for(const boundary of [outline,...holes]){const a=shift(boundary,-thickness/2),b=shift(boundary,thickness/2);for(let i=0;i<a.length;i++){const j=(i+1)%a.length;poly([a[i],a[j],b[j],b[i]],color);}}
 }
 function ring(center,outer,inner,width,color,n=12){
  const points=(x,r)=>Array.from({length:n},(_,i)=>[x,center[1]+r*Math.cos(i*2*Math.PI/n),center[2]+r*Math.sin(i*2*Math.PI/n)]);
  const a=points(center[0]-width/2,outer),b=points(center[0]+width/2,outer),c=points(center[0]-width/2,inner),d=points(center[0]+width/2,inner);
  for(let i=0;i<n;i++){const j=(i+1)%n;for(const q of [[a[i],a[j],c[j],c[i]],[b[i],b[j],d[j],d[i]],[a[i],a[j],b[j],b[i]],[c[i],c[j],d[j],d[i]]])poly(q,color);}
 }
 function arcRing(center,outer,inner,width,color,a0,a1,n=36){
  // Hollow cylinder along x, swept only from a0 to a1 (leaves the clamp slit open).
  const steps=Math.max(2,Math.ceil(Math.abs(a1-a0)/(2*Math.PI)*n));
  const pt=(x,r,a)=>[x,center[1]+r*Math.cos(a),center[2]+r*Math.sin(a)];
  const A=[],B=[],C=[],D=[];
  for(let i=0;i<=steps;i++){const a=a0+(a1-a0)*i/steps;A.push(pt(center[0]-width/2,outer,a));B.push(pt(center[0]+width/2,outer,a));C.push(pt(center[0]-width/2,inner,a));D.push(pt(center[0]+width/2,inner,a));}
  for(let i=0;i<steps;i++){const j=i+1;for(const q of [[A[i],A[j],C[j],C[i]],[B[i],B[j],D[j],D[i]],[A[i],A[j],B[j],B[i]],[C[i],C[j],D[j],D[i]]])poly(q,color);}
  poly([A[0],B[0],D[0],C[0]],color);poly([A[steps],B[steps],D[steps],C[steps]],color);
 }
 function boxAt(center,u,w,half,color){
  // Box whose axes are x (axial), u (radial, y-z pair) and w (tangential, y-z pair).
  const ex=[1,0,0],eu=[0,u[0],u[1]],ew=[0,w[0],w[1]],corners=[];
  for(const sx of[-1,1])for(const su of[-1,1])for(const sw of[-1,1]){let p=center.slice();for(const[v,s]of[[ex,sx*half[0]],[eu,su*half[1]],[ew,sw*half[2]]])p=p.map((x,i)=>x+v[i]*s);corners.push(p);}
  for(const ids of[[0,1,3,2],[4,5,7,6],[0,1,5,4],[2,3,7,6],[0,2,6,4],[1,3,7,5]])poly(ids.map(i=>corners[i]),color);
 }
 function cylBetween(a,b,r,color,n=12){
  const axis=[b[0]-a[0],b[1]-a[1],b[2]-a[2]],len=Math.hypot(...axis)||1,ax=axis.map(v=>v/len);
  const ref=Math.abs(ax[0])<0.9?[1,0,0]:[0,1,0];
  let u=[ax[1]*ref[2]-ax[2]*ref[1],ax[2]*ref[0]-ax[0]*ref[2],ax[0]*ref[1]-ax[1]*ref[0]];const ul=Math.hypot(...u)||1;u=u.map(v=>v/ul);
  const w=[ax[1]*u[2]-ax[2]*u[1],ax[2]*u[0]-ax[0]*u[2],ax[0]*u[1]-ax[1]*u[0]];
  const ringPts=c=>Array.from({length:n},(_,i)=>{const t=i/n*2*Math.PI,co=Math.cos(t)*r,si=Math.sin(t)*r;return[c[0]+u[0]*co+w[0]*si,c[1]+u[1]*co+w[1]*si,c[2]+u[2]*co+w[2]*si];});
  const A=ringPts(a),B=ringPts(b);
  for(let i=0;i<n;i++){const j=(i+1)%n;poly([A[i],A[j],B[j],B[i]],color);}
  poly(A,color);poly(B,color);
 }
 function clampHub(center,pinPoint,color){
  // Printed clamp hub on the O shaft: slitted barrel + ears; M3 screw only with hardware.
  const outer=(cfg.clamp_hub_outer_diameter_mm||16)/2,inner=(cfg.clamp_bore_mm||6.3)/2,width=cfg.clamp_hub_length_mm||10,slit=cfg.clamp_slit_mm||1.8;
  let dy=center[1]-pinPoint[1],dz=center[2]-pinPoint[2];const dl=Math.hypot(dy,dz)||1;dy/=dl;dz/=dl;
  const aS=Math.atan2(dz,dy),gap=Math.max(0.30,2*Math.asin(Math.min(0.95,(slit/2)/outer)));
  arcRing(center,outer,inner,width,color,aS+gap/2,aS+2*Math.PI-gap/2,36);
  const u=[dy,dz],w=[-dz,dy],earRadial=outer-1.5,earHalf=[Math.max(2,width/2-1),1.5,2.0],off=slit/2+earHalf[2];
  if(!cfg.l_link_reference)for(const s of[-1,1])boxAt([center[0],center[1]+u[0]*earRadial+w[0]*off*s,center[2]+u[1]*earRadial+w[1]*off*s],u,w,earHalf,color);
  if(hardware){
   const screwR=(cfg.clamp_screw_diameter_mm||3)/2,reach=off+earHalf[2];
   const at=(t,r)=>[center[0],center[1]+u[0]*r+w[0]*t,center[2]+u[1]*r+w[1]*t];
   cylBetween(at(-reach,earRadial),at(reach,earRadial),screwR,'#8795a3',10);
   cylBetween(at(-reach-1.8,earRadial),at(-reach,earRadial),2.75,'#8795a3',12);
   cylBetween(at(reach,earRadial),at(reach+1.8,earRadial),2.75,'#8795a3',12);
  }
 }
 function bar(a,b,color,bores=[]){
  const length=Math.hypot(b[1]-a[1],b[2]-a[2]),dy=-(b[2]-a[2])/length*cfg.link_width_mm/2,dz=(b[1]-a[1])/length*cfg.link_width_mm/2;
  prism([[a[0],a[1]+dy,a[2]+dz],[b[0],b[1]+dy,b[2]+dz],[b[0],b[1]-dy,b[2]-dz],[a[0],a[1]-dy,a[2]-dz]],t,color,bores);
 }
 for(const side of (cfg.two_wings?['R','L']:['R'])){
  const p=(name,end)=>parts[side+'/'+name][end];
  const O=p('crank1','p'),A=p('crank1','q'),D=p('crank2_direct','q'),S=p('rocker1','p'),B=p('rocker1','q'),E=p('inner_spar','q'),Q=p('elbow_horn','q'),T=p('outer_spar','q');
  const split=!!cfg.split_face;
  if(split){
   const OD=p('crank2_direct','p');
   bar(O,A,'#438bff',[[...O,cfg.screw_diameter_mm/2],A]);
   bar(OD,D,'#438bff',[[...OD,cfg.screw_diameter_mm/2],D]);
   ring([(O[0]+OD[0])/2,O[1],O[2]],cfg.screw_diameter_mm/2,0,Math.abs(OD[0]-O[0])+(cfg.two_wings?2*(t/2+cfg.clamp_hub_length_mm+5):4),'#8795a3',12);
   if(cfg.two_wings){
    const w=cfg.clamp_hub_length_mm;
    clampHub([O[0]-t/2-w/2,O[1],O[2]],A,'#438bff');
    clampHub([OD[0]+t/2+w/2,OD[1],OD[2]],D,'#438bff');
    // The two fixed crank hubs retain the input shaft axially; gear locking remains to be designed.
   }
   // No clamp hubs here: the 20 x 10 mm hub does not fit this concept's axial gaps (see build notes).
   if(structure&&!cfg.two_wings)ring([21.5,O[1],O[2]],7,0,5,'#687687',16);
  }else{prism([O,A,D],t,'#438bff',[[...O,cfg.bearing_bore_mm/2],A,D]);clampHub([O[0]+t/2+(cfg.clamp_hub_length_mm||10)/2,O[1],O[2]],[O[0],A[1]+D[1]-O[1],A[2]+D[2]-O[2]],'#438bff');}
  if(cfg.separate_strips){
   // Separate strips are offset for visibility; their rigid connectors are not designed yet.
   const at=(p,x)=>[x,p[1],p[2]];
   bar(S,E,'#ffe23b',[S,E]);
   bar(at(S,-26),at(B,-26),'#f8be34',[at(S,-26),at(B,-26)]);
   bar(at(B,-30),at(E,-30),'#ec9e28',[at(B,-30),at(E,-30)]);
  }else if(cfg.frame_wing){
   // Inset the triangle to make a single rigid frame, not three hinged bars.
   const dist=(a,b)=>Math.hypot(a[1]-b[1],a[2]-b[2]);
   const lengths=[dist(B,E),dist(E,S),dist(S,B)],perimeter=lengths.reduce((a,b)=>a+b,0);
   const center=[S[0],(lengths[0]*S[1]+lengths[1]*B[1]+lengths[2]*E[1])/perimeter,(lengths[0]*S[2]+lengths[1]*B[2]+lengths[2]*E[2])/perimeter];
   const area=Math.abs((B[1]-S[1])*(E[2]-S[2])-(B[2]-S[2])*(E[1]-S[1]))/2;
   const scale=Math.max(0,1-9/(2*area/perimeter));
   const cutout=[S,B,E].map(p=>[p[0],center[1]+scale*(p[1]-center[1]),center[2]+scale*(p[2]-center[2])]);
   prism([S,B,E],t,'#ffe23b',[S,B,E],scale>0?[cutout]:[]);
  }else prism([S,B,E],t,'#ffe23b',[S,B,E]);
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
  if(cfg.l_link_reference){
   // Follow the uploaded outline; only extend its long arm if the displayed E–T differs.
   const length=Math.hypot(outerT[1]-outerE[1],outerT[2]-outerE[2]);
   const uy=(outerT[1]-outerE[1])/length,uz=(outerT[2]-outerE[2])/length;
   const sign=Math.sign(uy*(Q[2]-outerE[2])-uz*(Q[1]-outerE[1]))||1;
   const point=([x,z],dx)=>{const along=x+Math.max(0,x-30)*(length-150)/120;return [outerE[0]+dx,outerE[1]+along*uy-z*uz*sign,outerE[2]+along*uz+z*uy*sign];};
   const ref=cfg.l_link_reference,shapes=[ref.outer,...ref.holes];
   const low=shapes.map(s=>s.map(p=>point(p,-t/2))),high=shapes.map(s=>s.map(p=>point(p,t/2)));
   poly(low[0],'#ffe23b',low.slice(1));poly(high[0],'#ffe23b',high.slice(1));
   for(let k=0;k<low.length;k++)for(let i=0;i<low[k].length;i++){const j=(i+1)%low[k].length;poly([low[k][i],low[k][j],high[k][j],high[k][i]],'#ffe23b');}
  }else{
   bar(outerE,Q,'#ffe23b',[outerE,Q]);
   if(cfg.separate_strips){const wingE=[outerE[0]+4,outerE[1],outerE[2]],wingT=[outerT[0]+4,outerT[1],outerT[2]];bar(wingE,wingT,'#f8be34',[wingE]);}
   else bar(outerE,outerT,'#ffe23b',[outerE]);
  }
  if(structure&&!cfg.two_wings){for(const x of (cfg.support_planes_x_mm||[cfg.support_plane_x_mm])){const oy=(O[1]+S[1])/2,oz=(O[2]+S[2])/2;prism([[x,oy-18,oz-29],[x,oy+18,oz-29],[x,oy+18,oz+29],[x,oy-18,oz+29]],4,'#536a7c',[[x,O[1],O[2]],[x,S[1],S[2]]]);if(split){ring([x,O[1],O[2]],cfg.bearing_outer_diameter_mm/2,cfg.bearing_bore_mm/2,cfg.bearing_width_mm,'#aebdca');ring([x,S[1],S[2]],cfg.bearing_outer_diameter_mm/2,cfg.bearing_bore_mm/2,cfg.bearing_width_mm,'#aebdca');}}}
  const joints=[['O',[O], '#438bff'],['A',[A,p('coupler1','p')],'#438bff'],['D',[D,p('rod2_direct','p')],'#438bff'],['S',[S],'#ffe23b'],['B',[B,p('coupler1','q')],'#ffe23b'],['E',[E,outerE],'#ffe23b'],['Q',[Q,p('rod2_direct','q')],'#438bff']];
  for(const[name,centers,color]of joints){
   if(name==='O')continue; // O carries the clamp hub instead of generic bearing/clip hardware.
   // Seats belong to the printed body; do not overlay extra plastic rings.
   if(!hardware&&!(highlight&&name==='D'))continue;
   const c=centers[0],xs=centers.map(p=>p[0]);if(cfg.two_wings&&name==='S')xs.push(...cfg.support_planes_x_mm);const lo=Math.min(...xs)-t/2-1,hi=Math.max(...xs)+t/2+1;
   for(const seat of centers)ring(seat,cfg.bearing_outer_diameter_mm/2,cfg.bearing_bore_mm/2,cfg.bearing_width_mm,'#aebdca');
   // A continuous screw axis, with hex head and nut outside the link stack.
   if(cfg.two_wings){
    if(name==='E'){
     // Large collar is on the triangle side; a thin retaining ring is schematic.
     ring([(lo+hi-5)/2,c[1],c[2]],3,0,hi-lo+15,'#8795a3',12);
     ring([lo-4,c[1],c[2]],10,3,8,'#aebdca',24);
     ring([hi+2.5,c[1],c[2]],5.5,3,1,'#aebdca',24);
    }else{
     ring([(lo+hi)/2,c[1],c[2]],3,0,hi-lo+10,'#8795a3',12);
     for(const x of [lo-2.5,hi+2.5])ring([x,c[1],c[2]],5.5,3,1,'#aebdca',24);
    }
   }
   else{ring([(lo+hi)/2,c[1],c[2]],cfg.screw_diameter_mm/2,0,hi-lo,'#8795a3',8);ring([lo-1,c[1],c[2]],cfg.head_diameter_mm/2,0,2,'#8795a3',24);ring([hi+cfg.nut_thickness_mm/2,c[1],c[2]],cfg.nut_across_flats_mm/2,cfg.screw_diameter_mm/2,cfg.nut_thickness_mm,'#8795a3',24);}
  }
 }
 if(cfg.two_wings&&structure){
  const get=(s,n)=>parts[s+'/'+n].p,rs=get('R','rocker1'),ls=get('L','rocker1'),ro=get('R','crank1'),lo=get('L','crank1');
  const extra=cfg.gear_stack?fr.gears.filter(g=>g.name.endsWith('idler')||g.name==='motor_pinion').map(g=>g.center):[];
  const pts=[rs,ls,ro,lo,...extra],ys=pts.map(p=>p[1]),zs=pts.map(p=>p[2]),y0=Math.min(...ys)-15,y1=Math.max(...ys)+15,z0=Math.min(...zs)-15,z1=Math.max(...zs)+15;
  for(const x of cfg.support_planes_x_mm){const holes=pts.map(p=>[x,p[1],p[2]]);prism([[x,y0,z0],[x,y1,z0],[x,y1,z1],[x,y0,z1]],4,'#536a7c',holes);for(const p of holes)ring(p,5,3,3,'#aebdca');}
  if(cfg.gear_stack&&hardware)for(const g of fr.gears.filter(g=>g.name.endsWith('idler')||g.name==='motor_pinion')){
   const p=g.center;
   if(g.name.endsWith('idler')){ring([-4.75,p[1],p[2]],3,0,40.5,'#8795a3');ring([-19.5,p[1],p[2]],10,3,8,'#aebdca');ring([14,p[1],p[2]],5.5,3,1,'#aebdca');}
   else{ring([14.75,p[1],p[2]],3,0,60.5,'#8795a3');for(const x of [-14,14])ring([x,p[1],p[2]],5.5,3,1,'#aebdca');}
  }
 }
}
