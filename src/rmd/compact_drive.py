"""Compact full mechanism: one motor and one reversing distribution gear pair.

The chosen gear spacing and shoulder spacing determine the input pivots.
Rotate A's complete four-bar about S, keeping its 50 mm ground length.
Increase the rocker-to-wing mounting offset by the same rotation, so wing
angles, link lengths and transmission angles stay exactly as synthesized.
Both input shafts counter-rotate, preserving exact bilateral symmetry.
The elbow geometry is translated unchanged. The original belt-driven variant stays intact.
"""
import itertools
import json
import numpy as np
from matplotlib.path import Path as PolygonPath

from .config import CONFIG_DIR, OUTPUT_DIR, FIXED, BUILD
from . import model
from .design_io import load_design
from .assembly import assembly_geometry, gear_outline
from .clearance import segment_distance, segment_triangle_distance


def settings():
    return json.loads((CONFIG_DIR/'compact_drive.json').read_text())


def layout(cfg):
    half = cfg['shoulder_spacing_mm']/2
    center = cfg['gear']['module_mm']*cfg['gear']['teeth']
    offset = center/2-half
    ground=cfg.get('ground_mm',model.D1)
    if half <= 0 or abs(offset) >= ground:
        raise ValueError('Compact layout cannot retain the synthesized ground length')
    o = np.array([offset, -np.sqrt(ground**2-offset**2)])
    rho = float(np.arctan2(o[1], o[0])-np.arctan2(model.O[1], model.O[0]))
    return half, o, rho


KEEP = {'crank1','coupler1','rocker1','inner_spar','outer_spar','crank2','rod2','elbow_horn',
        'pin_A','pin_B','pin_P','pin_Q','fastener_A','fastener_B','fastener_P','fastener_Q',
        'root_hub','elbow_hub','outer_wing_clamp','clamp_crank1','clamp_crank2','clamp_outer_horn'}
ROTATE = {'crank1','coupler1','rocker1','pin_A','pin_B','fastener_A','fastener_B','clamp_crank1'}


def transform(point, side, cfg, rotate=False):
    """Transform original mirrored Cartesian points to the compact layout."""
    p = np.asarray(point, dtype=float).copy()
    m = 1 if side == 'R' else -1
    half, _, rho = layout(cfg)
    uv = np.stack([m*p[...,1], p[...,2]], axis=-1)
    if rotate:
        c,s = np.cos(rho),np.sin(rho)
        uv = uv @ np.array([[c,s],[-s,c]])
    p[...,1] = m*(half+uv[...,0]);p[...,2] = uv[...,1]
    p[...,0] += cfg['left_axial_offset_mm'] if side == 'L' else 0
    return p


def geometry(design, sim, cfg):
    base=assembly_geometry(design,sim);parts={};n=len(sim['thetas'])
    half,o,_=layout(cfg)
    def axial(name,side,uv,start,end,radius,joint):
        m=1 if side=='R' else -1
        parts[name]={'p':np.tile([start,m*(half+uv[0]),uv[1]],(n,1)),
                     'q':np.tile([end,m*(half+uv[0]),uv[1]],(n,1)),
                     'radius':radius,'joints':{side+'/'+joint}}
    for name,p in base['parts'].items():
        side,label=name.split('/')
        if side not in ('R','L'):continue
        if label not in KEEP and '_finger_' not in label:continue
        parts[name]=dict(p,p=transform(p['p'],side,cfg,label in ROTATE),q=transform(p['q'],side,cfg,label in ROTATE))
    for side,dx in [('R',0),('L',cfg['left_axial_offset_mm'])]:
        axial(side+'/motor_shaft',side,o,6+dx,131 if side=='R' else 126,2.5,'O')
        axial(side+'/shoulder_shaft',side,model.S,-14+dx,126,2.5,'S')
        axial(side+'/gear_hub_O',side,o,cfg['local_gear_plane_x_mm']+3+dx,cfg['local_gear_plane_x_mm']+13+dx,13,'O')
        axial(side+'/gear_hub_S',side,model.S,cfg['local_gear_plane_x_mm']+3+dx,cfg['local_gear_plane_x_mm']+13+dx,13,'S')
        axial(side+'/distribution_hub',side,o,cfg['gear_plane_x_mm']+3,cfg['gear_plane_x_mm']+11,7,'O')
        # Elbow axle moves with the wing; all original joint lengths retained.
        old=base['parts'][side+'/elbow_shaft']
        parts[side+'/elbow_shaft']=dict(old,p=transform(old['p'],side,cfg),q=transform(old['q'],side,cfg))
    for label,start,end,r in [('motor_coupling',119.5,144.5,10),('motor_output_shaft',133,157,2.5)]:
        axial('R/'+label,'R',o,start,end,r,'O')
    boxes=[];plates=[]
    oy=half+o[0];oz=o[1]
    motor=cfg['motor']
    boxes.append({'name':'R/motor','center':[motor['front_face_x_mm']+motor['body_length_mm']/2,oy,oz],'size':[motor['body_length_mm'],motor['face_mm'],motor['face_mm']]})
    axial('R/motor_pilot','R',o,motor['front_face_x_mm']-motor['pilot_projection_mm'],motor['front_face_x_mm'],motor['pilot_diameter_mm']/2,'O')
    axial('R/unused_rear_motor_shaft','R',o,motor['front_face_x_mm']+motor['body_length_mm'],motor['front_face_x_mm']+motor['body_length_mm']+motor['rear_shaft_mm'],2.5,'O')
    boxes.append({'name':'base','center':cfg['base_center_mm'],'size':cfg['base_size_mm']})
    boxes.append({'name':'R/motor_support','center':[cfg['motor_mount_x_mm'],oy,(-116+oz-29)/2],'size':[4,14,oz-29+116]})
    plates.append({'name':'R/motor_mount','center':[cfg['motor_mount_x_mm'],oy,oz],'size':[4,58,58],
                   'holes':[[cfg['motor_mount_x_mm'],oy,oz]],'hole_radius':11.1})
    for x in cfg['bearing_plate_x_mm']:
        holes=[[x,m*(half+uv[0]),uv[1]] for m in (1,-1) for uv in (o,model.S)]
        plates.append({'name':f'common_bearing_plate_{x:g}','center':[x,0,-24],'size':[6,cfg['bearing_plate_width_mm'],122],
                       'holes':holes,'hole_radius':BUILD['bearing_fit_diameter_mm']/2})
        for y in cfg['frame_leg_y_mm']:
            boxes.append({'name':f'leg_{x:g}_{y:g}','center':[x,y,-100.5],'size':[6,12,31]})
    for y in cfg['frame_spacer_y_mm']:
        for z in (-80,32):
            parts[f'frame_spacer_{y}_{z}']={'p':np.tile([46,y,z],(n,1)),
                'q':np.tile([111,y,z],(n,1)),'radius':3,'joints':{'frame'}}
    panels={name:[transform(p,name[0],cfg) for p in quad] for name,quad in base['panels'].items()}
    from .assembly import add_root_bosses
    return add_root_bosses({'parts':parts,'panels':panels,'boxes':boxes,'plates':plates},'compact')


def gear_specs(theta,cfg):
    half,o,rho=layout(cfg);specs=[]
    gamma=model.GAMMA1+rho
    for side,m,dx in [('R',1,0),('L',-1,cfg['left_axial_offset_mm'])]:
        for name,uv,phase in [('drive',o,theta+rho),('shoulder',model.S,-theta+2*gamma+np.pi+np.pi/BUILD['gear']['teeth']-rho)]:
            specs.append({'name':side+'/'+name,'center':[cfg['local_gear_plane_x_mm']+dx,m*(half+uv[0]),uv[1]],
                          'phase':float(phase),'mirror':m,'profile':'local','face_width_mm':6})
    x=cfg['gear_plane_x_mm'];z=cfg['gear']['teeth']
    # Half-tooth clocking is relative to each independently clamped crank.
    specs.extend([{'name':'R/distribution','center':[x,half+o[0],o[1]],'phase':float(theta+rho),'mirror':1,'profile':'distribution','face_width_mm':6},
                  {'name':'L/distribution','center':[x,-half-o[0],o[1]],'phase':float(theta+rho-np.pi/z),'mirror':-1,'profile':'distribution','face_width_mm':6}])
    return specs


def audit(design,b1,b2,cfg,*,geometry_fn=None,gear_specs_fn=None):
    geometry_fn=geometry if geometry_fn is None else geometry_fn
    gear_specs_fn=gear_specs if gear_specs_fn is None else gear_specs_fn
    th=np.linspace(0,2*np.pi,cfg['audit_samples'],endpoint=False)
    sim=model.simulate(design,th,b1,b2);geom=geometry_fn(design,sim,cfg)
    sim=geom.get('simulation',sim)
    conflicts=[];minimum=np.inf;required=cfg['required_clearance_mm']
    def interval(p):
        half=p.get('axial_half_thickness',0) if np.allclose(p['p'][:,0],p['q'][:,0]) else 0
        return np.minimum(p['p'][:,0],p['q'][:,0])-half,np.maximum(p['p'][:,0],p['q'][:,0])+half
    def planar(p):
        q=p.copy();q[:,0]=0;return q
    for (name,p),(name2,q) in itertools.combinations(geom['parts'].items(),2):
        if p['joints']&q['joints']:continue
        a0,a1=interval(p);b0,b1_=interval(q);axial=np.maximum(b0-a1,a0-b1_)
        radial=segment_distance(planar(p['p']),planar(p['q']),planar(q['p']),planar(q['q']))-p['radius']-q['radius']
        gap=np.where((axial>0)|(radial>0),np.hypot(np.maximum(axial,0),np.maximum(radial,0)),np.maximum(axial,radial))
        if p.get('shape')=='capsule3d' or q.get('shape')=='capsule3d':
            gap=segment_distance(p['p'],p['q'],q['p'],q['q'])-p['radius']-q['radius']
        i=int(gap.argmin());minimum=min(minimum,float(gap[i]))
        if gap[i]<required-1e-8:conflicts.append({'parts':[name,name2],'gap_mm':float(gap[i]),'theta_deg':float(np.degrees(th[i]))})
    # Stationary structures, explicit bearing bores and intentional fastenings.
    for name,p in geom['parts'].items():
        a,b=p['p'],p['q'];x0,x1=interval(p)
        for box in geom['boxes']+geom['plates']:
            if 'frame_spacer_' in name and 'bearing_plate_' in box['name'] and ('/' not in name or box['name'].startswith(name.split('/')[0]+'/')):continue
            if name=='drive/output_shaft' and box['name']=='drive/actuator_reservation':continue # intended output into actuator
            if name in ('R/motor_output_shaft','R/motor_shaft','R/motor_pilot','R/unused_rear_motor_shaft') and box['name']=='R/motor':continue
            if box.get('holes'):
                coaxial=any(np.allclose(a[:,1:],np.array(h)[1:]) and np.allclose(b[:,1:],np.array(h)[1:]) for h in box['holes'])
                shaft_interface=('shaft' in name and p['radius']<=BUILD['shaft_diameter_mm']/2+1e-8)
                pilot_interface=(name=='R/motor_pilot' and box['name']=='R/motor_mount' and p['radius']<box['hole_radius'])
                if coaxial and (shaft_interface or pilot_interface):continue
            center=np.array(box['center']);halfbox=np.array(box['size'])/2
            axial=(x1>center[0]-halfbox[0]-required+1e-8)&(x0<center[0]+halfbox[0]+required-1e-8)
            lo=center-halfbox;hi=center+halfbox
            pad=np.array([0,p['radius']+required,p['radius']+required]);lo-=pad;hi+=pad
            dv=b-a;parallel=abs(dv)<1e-12;safe=np.where(parallel,1,dv)
            t1,t2=(lo-a)/safe,(hi-a)/safe
            lower=np.where(parallel,-np.inf,np.minimum(t1,t2));upper=np.where(parallel,np.inf,np.maximum(t1,t2))
            hit=axial&(np.maximum(lower[:,1:].max(axis=1),0)<=np.minimum(upper[:,1:].min(axis=1),1))&~np.any(parallel[:,1:]&((a[:,1:]<lo[1:])|(a[:,1:]>hi[1:])),axis=1)
            if p.get('shape')=='capsule3d':
                lo3=center-halfbox-p['radius']-required;hi3=center+halfbox+p['radius']+required
                t1,t2=(lo3-a)/safe,(hi3-a)/safe
                lower=np.where(parallel,-np.inf,np.minimum(t1,t2));upper=np.where(parallel,np.inf,np.maximum(t1,t2))
                hit=(np.maximum(lower.max(axis=1),0)<=np.minimum(upper.min(axis=1),1))&~np.any(parallel&((a<lo3)|(a>hi3)),axis=1)
            if hit.any():conflicts.append({'parts':[name,box['name']],'type':'structure','theta_deg':float(np.degrees(th[np.flatnonzero(hit)[0]]))})
        for panel,quad in geom['panels'].items():
            side=name.split('/')[0]
            supports_skin=(name.endswith('inner_spar') or '/inner_finger_' in name) and panel==side+'/inner_panel'
            supports_skin=supports_skin or ((name.endswith('outer_spar') or '/outer_finger_' in name) and panel==side+'/outer_panel')
            if supports_skin:continue
            aa,bb,cc,dd=quad
            distance=np.minimum(segment_triangle_distance(a,b,aa,bb,cc),segment_triangle_distance(a,b,aa,cc,dd))
            # A capsule encloses each flat link, cylinder or rib; conservative
            # near cylinder end faces and flat-link axial edges.
            skin=cfg.get('body_cover',{}).get('thickness_mm',0) if panel.startswith('body_cover/') else FIXED['membrane_thickness_mm']
            gap=distance-p['radius']-skin/2
            if gap.min()<required-1e-8:conflicts.append({'parts':[name,panel],'type':'full_part_panel_envelope','gap_mm':float(gap.min())})
    for name,quad in geom['panels'].items():
        vertices=np.stack(quad,axis=1);pmin=vertices.min(axis=1);pmax=vertices.max(axis=1)
        for box in geom['boxes']+geom['plates']:
            c=np.array(box['center']);h=np.array(box['size'])/2
            if np.any(np.all((pmax+required>=c-h)&(pmin-required<=c+h),axis=1)):
                conflicts.append({'parts':[name,box['name']],'type':'panel_structure_envelope'})
    for (name,panel),(other,quad) in itertools.combinations(geom['panels'].items(),2):
        if name.startswith('body_cover/') and other.startswith('body_cover/'):continue # one continuous stationary cover
        distances=[]
        for triangles,edges in [(panel,quad),(quad,panel)]:
            a,b,c,d=triangles
            for p,q in zip(edges,edges[1:]+edges[:1]):
                distances.append(np.minimum(segment_triangle_distance(p,q,a,b,c),segment_triangle_distance(p,q,a,c,d)))
        thickness=lambda n:cfg.get('body_cover',{}).get('thickness_mm',0) if n.startswith('body_cover/') else FIXED['membrane_thickness_mm']
        gap=np.minimum.reduce(distances)-(thickness(name)+thickness(other))/2
        if gap.min()<required-1e-8:conflicts.append({'parts':[name,other],'type':'panel_panel','gap_mm':float(gap.min())})
    structures=geom['boxes']+geom['plates']
    for a,b in itertools.combinations(structures,2):
        overlap=(np.array(a['size'])+np.array(b['size']))/2-np.abs(np.array(a['center'])-np.array(b['center']))
        if np.all(overlap>1e-8):conflicts.append({'parts':[a['name'],b['name']],'type':'stationary_structure_overlap','overlap_mm':overlap.tolist()})
    profiles={'local':BUILD['gear'],'distribution':cfg['gear']}
    specs=gear_specs_fn(0,cfg)
    for g in specs:
        center=np.tile(g['center'],(len(th),1));gx=g['center'][0];gh=g['face_width_mm']/2
        gp=profiles[g['profile']];radius=gp['module_mm']*(gp['teeth']/2+1)
        joint=g['name'].split('/')[0]+('/S' if g['name'].endswith('shoulder') else '/O')
        for name,p in geom['parts'].items():
            if joint in p['joints'] or name in g.get('interfaces',[]):continue
            x0,x1=interval(p)
            if not np.any((x1+required>=gx-gh)&(x0-required<=gx+gh)):continue
            radial=segment_distance(planar(p['p']),planar(p['q']),planar(center),planar(center))-radius-p['radius']
            if np.any(radial<required):conflicts.append({'parts':[name,g['name']],'type':'gear_envelope','gap_mm':float(radial.min())})
        for box in geom['boxes']+geom['plates']:
            c=np.array(box['center']);h=np.array(box['size'])/2
            if abs(gx-c[0])<gh+h[0]+required and np.linalg.norm(np.maximum(np.abs(center[0,1:]-c[1:])-h[1:],0))<radius+required:
                conflicts.append({'parts':[g['name'],box['name']],'type':'gear_structure'})
    penetrations=0
    for theta in np.linspace(0,2*np.pi/cfg['gear']['teeth'],121):
        specs=gear_specs_fn(theta,cfg)
        polygons=[gear_outline(g['phase'],g['mirror'],profiles[g['profile']])+np.array(g['center'])[1:] for g in specs]
        for i,j in itertools.combinations(range(len(specs)),2):
            if abs(specs[i]['center'][0]-specs[j]['center'][0])>6:continue
            p,q=polygons[i],polygons[j]
            penetrations+=int(PolygonPath(p).contains_points(q,radius=-1e-5).sum()+PolygonPath(q).contains_points(p,radius=-1e-5).sum())
    half,o,rho=layout(cfg)
    return {'status':'PASS' if not conflicts and not penetrations else 'FAIL',
            'scope':'Nominal full-cycle 3D envelope, stationary structures and coplanar gear-profile audit; not physical fit/load certification.',
            'samples':len(th),'conflict_count':len(conflicts),'conflicts':conflicts,'gear_vertex_penetrations':penetrations,
            'minimum_nonadjacent_part_clearance_mm':minimum,
            'shoulder_spacing_mm':2*half,'input_shaft_spacing_mm':cfg['gear']['module_mm']*cfg['gear']['teeth'],
            'input_offset_local_mm':o.tolist(),'assembly_rotation_deg':float(np.degrees(rho)),
            'rocker_mounting_offset_deg':float(np.degrees(design['kappa1']+rho)),
            'min_transmission_angle_deg':float(np.min(sim['mu1'])),
            'min_elbow_transmission_angle_deg':float(np.min(sim['mu2'])),
            'max_elbow_fold_deg':float(np.degrees(sim['F'].max())),
            'gear_count':len(gear_specs_fn(0,cfg)),'belt_count':1 if cfg.get('belt') else 0,
            'links_mm':{k:design[k] for k in ('a1','b1','c1')},'ground_mm':cfg.get('ground_mm',model.D1),
            'prototype_layout_passes':not conflicts and not penetrations,
            'build_ready':False,
            'limitations':['Trial bearing fits, hub clamps and axial retainers require hardware verification.',
                           'Controller and wiring not packaged; panel thickness/flex and loaded strength unverified.',
                           'Nominal gear polygons omit root fillets, manufacturing error and deflection.']}

