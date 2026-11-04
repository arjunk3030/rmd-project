"""Limited geometric screen for the top-mounted drive, not a build certification."""
import json
import numpy as np
from matplotlib.path import Path as PolygonPath
from .assembly import gear_outline
from .clearance import segment_triangle_distance
from .config import CONFIG_DIR
from .designs import get_direct
from .direct_drive import Problem, settings, gears
from . import direct_package
from .single_face import geometry as same_geometry


def check(layout):
    cfg=settings();trial=json.loads((CONFIG_DIR/'presentation/top_motor.json').read_text())
    if layout=='same':cfg.update(json.loads((CONFIG_DIR/'single_face.json').read_text()))
    v,ba,be,_=get_direct(allow_fit=False);p=Problem(720);sim=p.state(v,ba,be)['simulation']
    geom=same_geometry(sim,cfg) if layout=='same' else direct_package.geometry(sim,cfg)
    right=gears(0,cfg)[0];r=np.array(right['center']);beta=np.radians(trial['angle_above_right_gear_deg'])
    c=r.copy();c[1:]+=trial['center_distance_mm']*np.array([np.cos(beta),np.sin(beta)])
    n=len(sim['thetas']);items=[];removed={'body_pulley','pedestal_pulley','belt_span_-1','belt_span_1','drive/output_shaft'}
    checks=[('motor pinion',c[0]-1.5,c[0]+1.5,trial['motor_pinion_teeth']/2+1),
            ('motor shaft',c[0]+1.5,trial['motor_front_x_mm'],trial['shaft_diameter_mm']/2),
            ('motor envelope',trial['motor_front_x_mm'],trial['motor_front_x_mm']+trial['motor_length_mm'],trial['motor_face_mm']/np.sqrt(2))]
    for name,lo,hi,radius in checks:
        for label,part in geom['parts'].items():
            if label in removed:continue
            a,b=part['p'],part['q'];half=part.get('axial_half_thickness',0) if np.allclose(a[:,0],b[:,0]) else 0
            xlo=np.minimum(a[:,0],b[:,0])-half;xhi=np.maximum(a[:,0],b[:,0])+half;over=(xhi>=lo)&(xlo<=hi)
            if not over.any():continue
            vec=b[:,1:]-a[:,1:];den=np.maximum(np.sum(vec*vec,axis=1),1e-12)
            t=np.clip(np.sum((c[1:]-a[:,1:])*vec,axis=1)/den,0,1)
            gap=np.linalg.norm(a[:,1:]+t[:,None]*vec-c[1:],axis=1)-radius-part['radius'];minimum=float(gap[over].min())
            if minimum<1:items.append({'parts':[name,label],'gap_mm':minimum})
        start=np.broadcast_to([lo,*c[1:]],(n,3));end=np.broadcast_to([hi,*c[1:]],(n,3))
        for label,quad in geom['panels'].items():
            if label.startswith('body_cover/'):continue
            a,b,d,e=quad
            gap=np.minimum(segment_triangle_distance(start,end,a,b,d),segment_triangle_distance(start,end,a,d,e))-radius-.15
            if gap.min()<1:items.append({'parts':[name,label],'gap_mm':float(gap.min())})
    # Check sampled gear polygon vertices over one wing-gear tooth pitch.
    motor_gear=cfg['gear'].copy();motor_gear['teeth']=trial['motor_pinion_teeth'];motor_gear['face_width_mm']=3
    overlap=0;right_c=np.array(right['center'][1:]);top_c=c[1:]
    for t in np.linspace(0,2*np.pi/cfg['gear']['teeth'],121):
        phi=gears(t,cfg)[0]['phase'];top_phi=beta+np.pi-np.pi/motor_gear['teeth']+(cfg['gear']['teeth']/motor_gear['teeth'])*(beta-phi)
        a=gear_outline(phi,gear=cfg['gear'])+right_c;b=gear_outline(top_phi,gear=motor_gear)+top_c
        overlap+=int(PolygonPath(a).contains_points(b,radius=-1e-5).sum()+PolygonPath(b).contains_points(a,radius=-1e-5).sum())
    plate=next(b for b in geom['plates'] if abs(b['center'][0]-9.5)<.01)
    bearing_radius=trial['support_bearing_diameter_mm']/2
    existing_gap=min(np.linalg.norm(c[1:]-np.array(h)[1:])-bearing_radius-plate['hole_radius'] for h in plate['holes'])
    edge_gap=float(np.min(np.array(plate['size'][1:])/2-np.abs(c[1:]-np.array(plate['center'][1:]))-bearing_radius))
    return {'layout':layout,'samples':n,'new_motor_center_mm':c.tolist(),
            'motor_pinion_teeth':motor_gear['teeth'],'wing_gear_teeth':cfg['gear']['teeth'],
            'input_reduction':cfg['gear']['teeth']/motor_gear['teeth'],
            'rear_support_hole_diameter_mm':bearing_radius*2,'rear_support_min_existing_hole_web_mm':float(existing_gap),'rear_support_min_edge_web_mm':edge_gap,
            'detected_drive_conflicts':items,'sampled_gear_vertex_penetrations':overlap,
            'scope':'Preliminary envelope check of the new motor pinion, shaft and assumed box against modeled moving links and panels. Polygon vertex sampling is not a tooth-strength, fit or exact mesh test. Rear support plate requires a new bearing hole. Motor bracket, retention, tolerances, wiring, loaded behavior and gear stresses are not checked. Original same-face A–B/D collision is unchanged.',
            'build_ready':False}


def save_reports():
    from .config import OUTPUT_DIR
    for layout in ('split','same'):
        out=OUTPUT_DIR/'top_motor'/layout;out.mkdir(parents=True,exist_ok=True)
        report=check(layout)
        (out/'clearance.json').write_text(json.dumps(report,indent=2)+'\n')
        (out/'build_notes.md').write_text('''# Top motor concept

One motor drives an 18-tooth module-1 pinion which meshes with the existing right 34-tooth wing gear. The left 34-tooth gear still reverses the other wing. At a 15 rpm wing input the motor-pinion shaft turns approximately 28.3 rpm in the opposite direction (excluding any internal motor gearbox).

The illustrated motor is an assumed 40 × 20 × 20 mm envelope, not a selected motor. The pinion shaft extends from the gear plane at x = −4 mm to the motor at x = +34 mm. The rear frame plate needs an additional bearing opening. Shaft retention, the motor bracket, hub locking, gear thickness, print tolerances, actual tooth contact/strength, wiring, and motor torque have not been resolved.

clearance.json documents a limited sampled envelope check of the new drive; it is not a complete collision or loaded-strength validation. The original baseline check does not include this motor. The same-face option retains its existing A–B/D collision. Hand-check the printed gears and shafts before powered testing.
''')
        print(f'Top motor {layout}: {len(report["detected_drive_conflicts"])} limited-envelope conflicts; {report["sampled_gear_vertex_penetrations"]} sampled tooth vertices penetrating.',flush=True)
