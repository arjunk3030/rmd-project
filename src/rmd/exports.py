"""Build packets for both supported options, derived from checked coordinates."""
import csv
import json
import re
from pathlib import Path
import numpy as np
from .config import OUTPUT_DIR,BUILD,FIXED
from .assembly import gear_outline


def svg_header(w,h):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}"><rect width="100%" height="100%" fill="white"/>'


def _csv(path,header,rows):
    with path.open('w',newline='') as f:
        w=csv.writer(f);w.writerow(header);w.writerows(rows)


def _gear_pin(g,frame):
    name=g['name'].split('/')[0]+'/crank2_direct';pin=next(p for p in frame['parts'] if p['name']==name)['q']
    u=g['mirror']*(pin[1]-g['center'][1]);v=pin[2]-g['center'][2];c,s=np.cos(g['phase']),np.sin(g['phase'])
    return [float(c*u+s*v),float(-s*u+c*v)]


def export(kind,frames,meta,cfg,report,packet,geometry,params):
    out=OUTPUT_DIR/kind;out.mkdir(exist_ok=True);fr=frames[0]
    layout={'units':'mm; angles degrees in frame records, radians in synthesized parameter vectors',
        'design':kind,'package_inputs':cfg,'zero_pose':fr,'boxes':meta['boxes'],'plates':meta['plates'],
        'theta_zero':'Set to these coordinates before clamping hubs; positive theta is the direction used by the animation.',
        'generated_from':'The same full-assembly geometry used by clearance checks and animation.',
        'prototype_status':report['status'],'physical_build_verified':False}
    (out/'layout.json').write_text(json.dumps(layout,indent=2)+'\n')
    _csv(out/'motion.csv',['theta_deg','shoulder_deg','fold_deg','transmission_A_deg','transmission_elbow_deg'],
         [[f[k] for k in ('theta_deg','alpha_deg','F_deg','mu1_deg','mu2_deg')] for f in frames])
    _csv(out/'pivot_positions.csv',['theta_deg','part','endpoint','x_mm','y_mm','z_mm'],
         [[f['theta_deg'],p['name'],key,*p[key]] for f in frames for p in f['parts'] for key in ('p','q')])
    _csv(out/'rib_lengths.csv',['part','cut_center_distance_mm'],
         [[p['name'],np.linalg.norm(np.array(p['q'])-p['p'])] for p in fr['parts'] if '_finger_' in p['name']])
    # Nominal link profiles use explicit smooth pivot bores and widened shaft roots.
    link_names=['crank1','coupler1','rocker1','crank2','rod2','elbow_horn'] if kind=='compact' else ['crank1','coupler1','rocker1','crank2_direct','rod2_direct','elbow_horn']
    specs=[]
    for label in link_names:
        p=next(p for p in fr['parts'] if p['name']=='R/'+label);L=float(np.linalg.norm(np.array(p['q'])-p['p']))
        root=12 if label=='rocker1' and kind=='compact' else 6 if label in ('crank1','rocker1','crank2','elbow_horn') else 4
        bore=16.15 if label=='rocker1' and kind=='compact' else 5.2 if root>=6 else BUILD['pivot_hole_mm']
        if kind=='direct' and cfg.get('body_package'):root=4;bore=3.2
        specs.append({'name':label,'length':L,'root_radius':root,'root_bore':bore,'tip_bore':BUILD['pivot_hole_mm']})
    rows=[[s['name'],2,f"{s['length']:.4f}",'3 mm plywood trial stock; smooth metal 3 mm pivot surfaces; pin-center distances' if kind=='direct' else '3 mm plate; smooth 3 mm pivot surfaces; pin-center distances'] for s in specs]
    rows.extend([['wing covering',4,f"{FIXED['membrane_thickness_mm']} mm assumed",'Cut separate panels; hinge relief14 mm, never bridge the elbow with a taut sheet'],
                 ['support rib',10,'2 mm nominal diameter','Cut lengths in rib_lengths.csv'],
                 ['625 bearing',16 if kind=='compact' else 11,'5 x16 x5','Fit-test OD16.15 trial seats; retain outer races without rubbing inner races'],
                 ['5 mm smooth shafts','see shaft_schedule.csv','Ground metal rod','Retain axially using collars/spacers; confirm bearing fit'],
                 ['M3 pivot hardware',8,'Smooth 3 mm bearing surface','Use grip lengths in pivot_hardware.csv; threads are not bearing surfaces'],
                 ['motor',1,cfg['motor']['candidate'],'2 A/phase candidate, 0.59 Nm HOLDING specification; dynamic torque unverified'],
                 ['STEP/DIR current-controlled driver',1,'Match motor and supply','Configure current/microsteps physically; firmware does not set driver current'],
                 ['base',1,' x '.join(map(str,cfg['base_size_mm'])),'Nominal supported layout; fasten frame legs and motor mount'],
                 ['axial collars and bearing retainers','as needed','5 mm bore collars; low-profile outer-race retainers','Final retaining stack must stay inside modeled envelopes; hand-check fits and axial freedom']])
    if kind=='direct' and cfg.get('body_package'):
        rows=[r for r in rows if r[0] not in ('625 bearing','5 mm smooth shafts','STEP/DIR current-controlled driver','motor','axial collars and bearing retainers')]
        rows.extend([['plain bushing',10,'3 mm ID x 6 mm OD x 3 mm long','Trial sleeve size, measure running fit; no 16 mm ball bearings'],
          ['3 mm steel shafts','see shaft_schedule.csv','3 mm OD','Small metal hubs/retainers, grip unverified'],
          ['continuous actuator',1,cfg['motor']['candidate'],'Pedestal reservation only; actual torque, output and driver selection pending'],
          ['timing belt',1,'2 mm pitch, 240 mm pitch length, 6 mm width','100 mm centers with two 20T pulleys; allow adjustable tension'],
          ['timing pulley',2,'20T, 2 mm pitch, 6 mm face','3 mm shaft hub in body, adapt pedestal pulley to selected actuator']])
    gear_set=[]
    for i,g in enumerate(fr['gears']):
        gear=cfg['gear'] if g['profile']=='distribution' else BUILD['gear']
        pin=_gear_pin(g,fr) if kind=='direct' and not cfg.get('body_package') else None
        gear_set.append((g,gear,pin));rows.append([g['name'],1,f"{gear['teeth']}T module{gear['module_mm']}; face{gear['face_width_mm']}",
            '6 mm laminated-plywood gear web carries rear crank pin; attach to metal shaft hub' if pin else 'Clamped gear; zero-pose tooth phase is in layout.json'])
    if kind=='direct' and not cfg.get('body_package'):rows.append(['second crank arm',0,f"throw {params[5]:.4f}",'Integrated in each rear gear web; do not fabricate a separate floating shoulder crank'])
    for plate in meta['plates']:
        rows.append([plate['name'],1,' x '.join(map(str,plate['size'])),
                     'Bearing/pilot center template supplied; finish retaining seats and frame mounting holes against purchased hardware'])
    for box in meta['boxes']:
        if box['name'].endswith('/motor') or box['name']=='base':continue
        rows.append([box['name'],1,' x '.join(map(str,box['size'])),
                     'Structural envelope; finish mounting/fastening details in CAD'])
    for part in fr['parts']:
        if any(tag in part['name'] for tag in ('clamp','frame_spacer')):
            rows.append([part['name'],1,f"length {np.linalg.norm(np.array(part['q'])-part['p']):.3f}; envelope radius {part['radius']}",
                         'Envelope allocation; select or finish clamp/spacer and verify grip and retention'])
    if cfg.get('body_cover',{}).get('enabled'):
        rows.append(['bat body silhouette',1,'3 mm plywood; bat_body_1to1.svg','Removable front cover; brackets/fasteners require final layout. Do not enclose moving rods with taut fabric.'])
    _csv(out/'parts.csv',['part','quantity','size_mm_or_specification','notes'],rows)
    shafts=[];pivots=[]
    for p in fr['parts']:
        if p['name'].endswith(('motor_shaft','shoulder_shaft','elbow_shaft')):
            note='Supplied motor rotor: 24 front / 13 rear projections; do not cut this as a stock shaft' if kind=='direct' and not cfg.get('body_package') and p['name']=='R/motor_shaft' else ('Smooth 3 mm metal shaft; short span supported in plain bushings' if cfg.get('body_package') else 'Smooth 5 mm stock; endpoints include nominal collar/engagement allowance')
            shafts.append([p['name'],float(np.linalg.norm(np.array(p['q'])-p['p'])),*p['p'],*p['q'],note])
        if '/pin_' in p['name']:
            name=p['name'].split('/pin_')[1];thickA=6 if kind=='direct' and not cfg.get('body_package') and name=='D' else BUILD['link_thickness_mm']
            grip=abs(p['p'][0]-p['q'][0])+(0 if cfg.get('body_package') else (thickA+BUILD['link_thickness_mm'])/2)
            pivots.append([p['name'],grip,2,6,'M3 button head/thin jam nut and washers, <=2 mm beyond each part; smooth 3 mm grip'])
    _csv(out/'shaft_schedule.csv',['shaft','length_mm','x0','y0','z0','x1','y1','z1','note'],shafts)
    _csv(out/'pivot_hardware.csv',['pivot','minimum_smooth_grip_mm','max_head_or_nut_stack_mm','head_OD_envelope_mm','note'],pivots)
    # Link drilling templates, true 1:1 physical units.
    width=max(s['length'] for s in specs)+65;height=len(specs)*28+18
    svg=[svg_header(width,height)]
    for i,s in enumerate(specs):
        x,y=18,16+i*28;L=s['length'];r=s['root_radius']
        svg.extend([f'<path d="M{x},{y-4}H{x+L}A4,4 0 0 1 {x+L},{y+4}H{x}A4,4 0 0 1 {x},{y-4}Z" fill="none" stroke="black" stroke-width=".15"/>',
            f'<circle cx="{x}" cy="{y}" r="{r}" fill="none" stroke="black" stroke-width=".15"/>',
            f'<circle cx="{x}" cy="{y}" r="{s["root_bore"]/2}" fill="none" stroke="black" stroke-width=".15"/>',
            f'<circle cx="{x+L}" cy="{y}" r="{s["tip_bore"]/2}" fill="none" stroke="black" stroke-width=".15"/>',
            f'<text x="{x+L+7}" y="{y+1}" font-size="3">{s["name"]}: {L:.3f}</text>'])
    svg.append('</svg>');(out/'link_drilling_1to1.svg').write_text('\n'.join(svg))
    # Each gear's canonical tooth outline and actual drive-pin drilling position.
    for i,(g,gear,pin) in enumerate(gear_set):
        r=gear['module_mm']*(gear['teeth']/2+1);c=r+5;outline=gear_outline(0,gear=gear)+c
        svg=[svg_header(2*c,2*c),'<polygon points="'+' '.join(f'{u:.5f},{v:.5f}' for u,v in outline)+'" fill="none" stroke="black" stroke-width=".12"/>',
            f'<circle cx="{c}" cy="{c}" r="{1.6 if cfg.get('body_package') else 2.6}" fill="none" stroke="black" stroke-width=".12"/>']
        if pin:svg.append(f'<circle cx="{c+pin[0]}" cy="{c+pin[1]}" r="1.6" fill="none" stroke="black" stroke-width=".12"/>')
        svg.append('</svg>');(out/('gear_'+g['name'].replace('/','_')+'_1to1.svg')).write_text('\n'.join(svg))
    for plate in meta['plates']:
        sy,sz=plate['size'][1:];cy,cz=plate['center'][1:];svg=[svg_header(sy+20,sz+20),f'<rect x="10" y="10" width="{sy}" height="{sz}" fill="none" stroke="black" stroke-width=".15"/>']
        for h in plate['holes']:
            y,z=h[1]-cy+sy/2+10,cz+sz/2+10-h[2]
            svg.append(f'<circle cx="{y}" cy="{z}" r="{plate["hole_radius"]}" fill="none" stroke="black" stroke-width=".15"/>')
        svg.append('</svg>');(out/('plate_'+plate['name'].replace('/','_')+'_1to1.svg')).write_text('\n'.join(svg))
    # Unfold each wing panel along an orthonormal basis; pitch does not distort cut dimensions.
    svg=[svg_header(210,230)]
    for i,name in enumerate(('R/inner_panel','R/outer_panel')):
        q=np.array(fr['panels'][name]);e=q[1]-q[0];e/=np.linalg.norm(e);n=np.cross(e,q[3]-q[0]);n/=np.linalg.norm(n);c=np.cross(n,e)
        flat=np.column_stack(((q-q[0])@e,(q-q[0])@c));flat-=flat.min(axis=0);flat+=[12,12+i*105]
        svg.append('<polygon points="'+' '.join(f'{x:.4f},{y:.4f}' for x,y in flat)+'" fill="none" stroke="black" stroke-width=".15"/>')
        svg.append(f'<text x="12" y="{i*105+103}" font-size="3">{name}: mirror for left; print100%; separate hinge panels.</text>')
    svg.append('</svg>');(out/'wing_panels_1to1.svg').write_text('\n'.join(svg))
    cover=cfg.get('body_cover',{})
    if cover.get('enabled'):
        outline=cover['outline_yz_mm'];ys=[p[0] for p in outline];zs=[p[1] for p in outline]
        width=max(ys)-min(ys);height=max(zs)-min(zs)
        points=' '.join(f'{y-min(ys)+5:.3f},{max(zs)-z+5:.3f}' for y,z in outline)
        (out/'bat_body_1to1.svg').write_text(svg_header(width+10,height+10)+f'<polygon points="{points}" fill="none" stroke="black" stroke-width=".15"/></svg>')
    _cad(out,kind,fr,meta,cfg,specs,gear_set)
    _notes(out,kind,report,cfg,fr)
    # All motion plots use the exact solved assembly, not merely guessed targets.
    import matplotlib.pyplot as plt
    from . import targets
    t=np.radians([f['theta_deg'] for f in frames]);
    if kind=='direct' and cfg.get('motion_targets'):
        from .direct_targets import curves
        target_a,target_f=curves(t,cfg)
    else:target_a=np.array([targets.alpha_target(x) for x in t]);target_f=np.array([targets.F_target(x) for x in t])
    fig,ax=plt.subplots(2,1,figsize=(9,6),sharex=True)
    ax[0].plot(np.degrees(t),[f['alpha_deg'] for f in frames],label='Solved shoulder');ax[0].plot(np.degrees(t),np.degrees(target_a),'--',label='Estimated target');ax[0].set_ylabel('Shoulder (deg)');ax[0].legend()
    ax[1].plot(np.degrees(t),[f['F_deg'] for f in frames],label='Solved fold');ax[1].plot(np.degrees(t),np.degrees(target_f),'--',label='Estimated target');ax[1].set_ylabel('Elbow fold (deg)');ax[1].set_xlabel('Input crank (deg)');ax[1].legend();fig.tight_layout();fig.savefig(out/'motion.png',dpi=140);plt.close(fig)
    from .animate3d import draw_frame
    fig=plt.figure(figsize=(11,7));ax=fig.add_subplot(111,projection='3d');draw_frame(ax,frames[0],meta);fig.savefig(out/'preview.png',dpi=140);plt.close(fig)
    draw_fold=max(frames,key=lambda x:x['F_deg']);fig=plt.figure(figsize=(11,7));ax=fig.add_subplot(111,projection='3d');draw_frame(ax,draw_fold,meta);fig.savefig(out/'max_fold.png',dpi=140);plt.close(fig)


def _cad(out,kind,frame,meta,cfg,specs,gear_set):
    common='''$fn=48;
module axle(p,q,r){translate([min(p[0],q[0]),p[1],p[2]])rotate([0,90,0])cylinder(h=abs(q[0]-p[0]),r=r);}
module rod(p,q,r){d=q-p;L=norm(d);translate(p)rotate(a=acos(d[2]/L),v=(abs(d[0])+abs(d[1])<.00001?[1,0,0]:[-d[1],d[0],0]))cylinder(h=L,r=r);}
module flat(p,q,r){translate([p[0]-1.5,0,0])rotate([0,90,0])linear_extrude(3)hull(){translate([-p[2],p[1]])circle(r=r);translate([-q[2],q[1]])circle(r=r);}}
'''
    assembly=['// Nominal checked assembly envelopes; finished individual flat/gear drilling in parts.scad.',common]
    for p in frame['parts']:
        a,b=p['p'],p['q'];name=p['name']
        kindfn='rod' if '_finger_' in name else 'axle' if a[0]!=b[0] else 'flat'
        assembly.append(f'{kindfn}({json.dumps(a)},{json.dumps(b)},{p["radius"]}); // {name}')
    for b in meta['boxes']+meta['plates']:
        assembly.append(f'difference(){{translate({json.dumps(b["center"])})cube({json.dumps(b["size"])},center=true);')
        for h in b.get('holes',[]):assembly.append(f'axle({json.dumps([h[0]-4,*h[1:]])},{json.dumps([h[0]+4,*h[1:]])},{b["hole_radius"]});')
        assembly.append('}')
    for g,gear,pin in gear_set:
        ps=gear_outline(g['phase'],g['mirror'],gear);poly=np.column_stack((-ps[:,1],ps[:,0]))
        assembly.append(f'color("steelblue")translate({json.dumps([g["center"][0]-gear['face_width_mm']/2,*g["center"][1:]])})rotate([0,90,0])linear_extrude({gear["face_width_mm"]})polygon(points={json.dumps(poly.tolist())});')
    for q in meta.get('covers',[]):assembly.append(f'color([.08,.06,.1])polyhedron(points={json.dumps(q)},faces=[[0,1,2],[0,2,3]]); // stationary cover mid-surface; thickness in config')
    for name,q in frame['panels'].items():assembly.append(f'color([.2,.6,.5,.4])polyhedron(points={json.dumps(q)},faces=[[0,1,2],[0,2,3]]); // {name}: membrane reference')
    (out/'assembly_reference.scad').write_text('\n'.join(assembly)+'\n')
    parts=['// Printable/cuttable nominal drilling profiles. Verify fits; finish hub clamps/retainers in CAD.',
           'part="link_crank1"; $fn=72;',
           'module link(L,r,bore,tip){difference(){linear_extrude(3)union(){hull(){circle(r=4);translate([L,0])circle(r=4);}circle(r=r);}translate([0,0,-1])cylinder(h=5,d=bore);translate([L,0,-1])cylinder(h=5,d=tip);}}']
    for s in specs:parts.append(f'if(part=="link_{s["name"]}")link({s["length"]},{s["root_radius"]},{s["root_bore"]},{s["tip_bore"]});')
    for i,(g,gear,pin) in enumerate(gear_set):
        key=g['name'].replace('/','_');outline=gear_outline(0,gear=gear).tolist();hub=3 if kind=='direct' else 10
        if cfg.get('body_package'):
            parts.append(f'if(part=="gear_{key}")difference(){{linear_extrude(3)polygon(points={json.dumps(outline)});translate([0,0,-1])cylinder(h=5,d=3.2);}}')
            continue
        parts.append(f'if(part=="gear_{key}")difference(){{union(){{linear_extrude(6)polygon(points={json.dumps(outline)});translate([0,0,6])cylinder(h={hub},r=9);}}translate([0,0,-1])cylinder(h={8+hub},d=5.2);')
        if pin:parts.append(f'translate({json.dumps([*pin,-1])})cylinder(h={8+hub},d=3.2);')
        parts.extend([f'translate([2,-.6,5])cube([10,1.2,{hub+2}]);',f'translate([6.5,-12,6.5])rotate([-90,0,0])cylinder(h=24,d=3.2);','}'])
    parts.append('// Gear root fillets, clamp nut seats, bearing retainers and purchased hardware interfaces require fit verification.')
    (out/'parts.scad').write_text('\n'.join(parts)+'\n')


def _notes(out,kind,report,cfg,frame):
    if cfg.get('body_package'):
        from .small_body_notes import write_notes
        return write_notes(out,report,cfg)
    k=report['kinematics'];load=report['loads'];direct=kind=='direct'
    text=f'''# {report['name']} — prototype build packet

Nominal motion/layout status: **{report['status']}**. Physical build verification: **not completed**.
All lengths are mm. Angles in motion.csv are degrees; dimension vectors use radians.

## Mechanism and power path

'''
    if direct:text+='''One dual-shaft motor drives A from its front shaft and the elbow directly from a
pin in the gear on its rear shaft. The mating gear reverses the passive left O
shaft. The two cranks are on the **same axis**, separated front/back; there is no
second control lever or powered input at S. Two gears total. The shoulder rocker
and inner wing are clamped to the S output shaft. The elbow horn and outer wing
are clamped to the E axle, which turns in two bearings carried by the inner wing.

The 13 mm rear motor stub is short: gear face6 + hub3 occupy9 mm of shaft at
x52..61; the gear web itself carries the crank pin. There is no separate rear
crank hub stacked outside that stub. Do not substitute a longer hub without
rechecking shaft engagement and rod clearance.
'''
    else:text+='''The motor turns right O; one30T gear pair reverses left O. Each local O–S 50T pair
turns the S shaft and B crank. A's rocker and the inner wing rotate **on bearings
around S**, independently of that shaft. Do not clamp A's rocker to the B shaft.
B's rod drives the outer-wing horn at E. Six gears total; one motor; no belts.
'''
    if direct:text+='''
## Wood, fabric and tighter packaging

Flat links are assumed 3 mm plywood; gears provisionally use two laminated
3 mm layers. Use metal shaft hubs, smooth metal pins, washers and spacers. Wood
quality, grain, pivot-hole wear/tear-out and fabric tension need bench tests.
Density and 2 GPa effective rod stiffness are editable estimates, not measured
properties. Wing masses remain guessed values until the assemblies are weighed.

Both same-side rod orders were rejected: one rod crosses the other crank pin
or the shared shaft during a cycle. The retained mechanism keeps the original
opposite-end layout and reduces each crank-to-rod offset from 10 to 8.5 mm.
No servo substitution has been modeled; the retained motor is still dual-shaft.

`bat_body_1to1.svg` is a removable 3 mm front silhouette, 104 mm wide and
119 mm tall, at x=-36 mm. Its finite thickness is included in moving-part and
fabric clearance checks. Cosmetic cover pieces touch each other intentionally.
Cover brackets/fasteners are not designed; mount them on the stationary frame
and check them before use. Hide the cover in the viewer to inspect the links.
Keep the mechanism open behind the face; a tight fabric wrap could snag it.
'''
    text+=f'''
## What is chosen versus synthesized

- `config/targets.json`: editable estimated animal-like motion, not measured biology.
- `config/layout.json`: chosen wing lengths, cover pitch/chords and hinge relief.
- `config/{'direct_drive' if direct else 'compact_drive'}.json`: chosen package, motor envelope and numerical bounds.
- `dimensions.json`: synthesized lengths/phases; `layout.json`: derived actual3D coordinates.
- Mass, friction and material stiffness in `config/build.json` are assumptions.

## Assembly sequence

1. Buy/measure the motor, bearings, shafts and pivot hardware before final printing.
   Make bearing-seat and5mm shaft/clamp coupons. The suggested16.15 seat is a trial
   dimension. Bearing OD seats must retain outer races; relieve the inner-race
   faces so rotating shafts/inner races do not rub the printed housing.
2. Use the per-plate1:1 SVGs for shaft-center positions. Plate bores are shown at
   bearing OD; finish an outer-race seat/retainer rather than leaving a bearing
   loose in a through-hole. Space the frame to the X coordinates in layout.json.
3. Cut shafts using shaft_schedule.csv. Install spacers and axial collars with
   slight running clearance; no free shaft or bearing should walk sideways.
   Retaining details must stay inside the checked link/hub/fastener envelopes.
4. Fabricate the flat links using link_drilling_1to1.svg or parts.scad. Smooth
   pivot bearing surfaces are3mm nominal; drill/ream3.2mm trial holes. Use the
   smooth grip lengths from pivot_hardware.csv. Do not run on screw threads.
5. Assemble at theta=0 using layout.json endpoint coordinates, then clamp the
   crank/gear mounting phases. Left and right tooth phases differ; use each
   side's gear SVG. Hand-turn a full revolution in the positive modeled direction.
6. Fit the light ribs and separate pitched/tapered covers. Keep14mm free around
   the elbow on each panel; a taut sheet across that gap would add an unmodeled
   spring/load. Check the complete cycle again with actual panel thickness.
7. Connect one STEP/DIR driver, set current/microsteps to the actual hardware,
   and use firmware/wing_drive.ino. Its DIR level is wiring-dependent: the elbow
   must fold on the return stroke shown in the animation. Start slowly, then ramp
   to the modeled15rpm. No homing, stall detection or closed-loop force control
   is implemented.

## Checked numerical results

- Input crank makes360°; closure residual {k['cycle_closure_error_mm']:.2g} mm.
- Minimum transmission: A {k['mu1_min_deg']:.2f}°, elbow {k['mu2_min_deg']:.2f}°.
- Fold range {k['min_F_deg']:.2f}°..{k['max_F_deg']:.2f}°; core downstroke max {k['max_F_core_downstroke_deg']:.2f}°.
- {report['clearance']['samples']} full-cycle poses; {report['clearance']['conflict_count']} modeled conflicts.
- Nonadjacent moving-part envelope gap {report['clearance']['minimum_nonadjacent_part_clearance_mm']:.2f} mm minimum.
- Estimated running torque target {load['required_running_torque_target_Nm']:.3f} Nm at15rpm, including an assumed startup/friction/service allowance.

## Remaining real-build questions

The motor's0.59Nm specification is **holding torque**, not verified running
capacity. Compare the actual driver/supply running curve and test it. Masses,
stock stiffness, friction, fits and clamp slip are unmeasured. The load estimate
checks a conditional elbow-shaft/rod case, not every pin, bearing or gear tooth.
The energy model omits aerodynamic load, impacts, compliance and resonance.
Changing from0.25Hz to a faster wingbeat changes inertia loads with speed squared.

The SCAD assembly is a checked-envelope reference. Individual flat/gear profiles
have drilling geometry, but root fillets, nut/insert seats and final bearing/
shaft retaining details still need finishing against purchased hardware. These
SCAD files were syntax-inspected, not rendered by OpenSCAD in this environment.
Nothing here certifies a flight-capable or strength-qualified machine.
'''
    (out/'build_notes.md').write_text(text)


def write_index():
    rows=[]
    for kind in ('compact','direct'):
        path=OUTPUT_DIR/kind/'validation.json'
        if not path.exists():continue
        r=json.loads(path.read_text());rows.append(f'<article><h2>{r["name"]}</h2><p>Nominal checks: {r["status"]} · {r["clearance"]["gear_count"]} gears · fold {r["kinematics"]["max_F_deg"]:.1f}°</p><a href="{kind}_3d.html">Open interactive3D</a> · <a href="{kind}/build_notes.md">Build notes</a><br><img src="{kind}/preview.png" width="500"></article>')
    (OUTPUT_DIR/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Two compact bat-wing designs</title><style>body{font:16px system-ui;background:#11151c;color:#ddd;margin:32px}a{color:#8fc4ff}main{display:flex;gap:24px;flex-wrap:wrap}article{max-width:520px}img{max-width:100%}</style><h1>Two compact bat-wing designs</h1><p>One motor each. All targets are editable engineering estimates. Nominal checks do not replace hardware fit and loaded testing.</p><main>'+''.join(rows)+'</main>')
    # Preserve the user-referenced path as a redirect, not a third design.
    alias=OUTPUT_DIR/'experiments/coaxial';alias.mkdir(parents=True,exist_ok=True)
    (alias/'interactive_3d.html').write_text('<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=../../direct_3d.html"><a href="../../direct_3d.html">The direct-shaft design moved here.</a>')
