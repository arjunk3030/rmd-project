"""Independent full-cycle motion checks and explicit hardware assumptions."""
import numpy as np
from .config import SCREENS,BUILD
from . import model,targets
from .fourbar import grashof_crank_rocker


def motion(sim,kind,params,source_design,cfg,assemble):
    t=sim['thetas'];n=len(t);at=np.array([targets.alpha_target(x) for x in t]);ft=np.array([targets.F_target(x) for x in t])
    alpha=sim['alpha'];fold=sim['F'];down=np.roll(alpha,-1)<np.roll(alpha,1);up=~down
    if kind=='direct' and cfg.get('motion_targets'):
        from .direct_targets import curves
        at,ft=curves(t,cfg)
    core=(np.degrees(t)>=45)&(np.degrees(t)<=135)&down
    if kind=='compact':
        a,b,c=source_design['a1'],source_design['b1'],source_design['c1'];O=model.O
        a2,h,L=source_design['a2'],source_design['c2'],source_design['b2'];O2=model.S
    else:
        a,b,c,k,pa,a2,pd,h,eta,L=params;from .compact_drive import layout
        O=layout(cfg)[1];O2=O
    ground=float(np.linalg.norm(O-model.S))
    def err(p,q,L):return float(abs(np.linalg.norm(p-q,axis=1)-L).max())
    length=max(err(sim['A1'],O,a),err(sim['B1'],sim['A1'],b),err(sim['B1'],model.S,c),
               err(sim['E'],model.S,sim.get('inner_length_mm',model.L_IN)),err(sim['P2'],O2,a2),err(sim['Q2'],sim['P2'],L),err(sim['Q2'],sim['E'],h))
    seam=assemble(np.array([0.,2*np.pi]));closure=max(np.linalg.norm(seam[k][1]-seam[k][0]) for k in ('A1','B1','E','P2','Q2','TIP'))
    angle=np.unwrap(np.r_[np.arctan2((sim['A1']-O)[:,1],(sim['A1']-O)[:,0]),np.arctan2((sim['A1']-O)[0,1],(sim['A1']-O)[0,0])])
    rotation=float(abs(np.degrees(angle[-1]-angle[0])))
    rep={'samples':n,'step_deg':360/n,'first_crank_rotation_deg':rotation,
         'mu1_min_deg':float(sim['mu1'].min()),'mu2_min_deg':float(sim['mu2'].min()),
         'min_F_deg':float(np.degrees(fold.min())),'max_F_deg':float(np.degrees(fold.max())),
         'peak_fold_theta_deg':float(np.degrees(t[fold.argmax()])),
         'max_F_downstroke_deg':float(np.degrees(fold[down].max())),
         'max_F_core_downstroke_deg':float(np.degrees(fold[core].max())) if core.any() else 1e9,
         'rms_alpha_deg':float(np.degrees(np.sqrt(np.mean((alpha-at)**2)))),
         'rms_F_upstroke_deg':float(np.degrees(np.sqrt(np.mean((fold[t>np.pi]-ft[t>np.pi])**2)))),
         'max_link_length_error_mm':length,'cycle_closure_error_mm':float(closure),
         'fixed_assembly_branches':True,'first_crank_is_shortest':bool(a<min(b,c,ground)),
         'second_loop_classification':'moving-base crank-rocker' if kind=='compact' else 'coupled six-bar; Grashof does not apply separately to the elbow loop'}
    checks={'assembles_full_cycle':bool(sim['ok']), 'full_input_rotation':abs(rotation-360)<1e-7,
            'first_loop_Grashof':grashof_crank_rocker(a,b,c,ground),
            'transmission_shoulder':rep['mu1_min_deg']>=SCREENS['mu_min_deg'],
            'transmission_elbow':rep['mu2_min_deg']>=SCREENS['mu_min_deg'],
            'no_hyperextension':rep['min_F_deg']>=-SCREENS['hyperextension_tol_deg']-1e-8,
            'downstroke_fold':rep['max_F_downstroke_deg']<=SCREENS['downstroke_fold_tol_deg']+1e-6,
            'core_downstroke_straightness':rep['max_F_core_downstroke_deg']<=SCREENS['core_downstroke_fold_max_deg']+1e-6,
            'peak_fold':SCREENS['fold_peak_min_deg']<=rep['max_F_deg']<=SCREENS['fold_peak_max_deg'],
            'peak_on_upstroke':bool(up[fold.argmax()]),
            'shoulder_target_fit':rep['rms_alpha_deg']<=SCREENS['shoulder_rms_max_deg'],
            'upstroke_target_fit':rep['rms_F_upstroke_deg']<=SCREENS['upstroke_fold_rms_max_deg'],
            'rigid_lengths':length<1e-7,'cycle_closure':closure<1e-7}
    if kind=='direct' and cfg.get('motion_acceptance'):
        limits=cfg['motion_acceptance']
        checks.update(transmission_shoulder=rep['mu1_min_deg']>=cfg.get('minimum_transmission_deg',40),
            transmission_elbow=rep['mu2_min_deg']>=cfg.get('minimum_transmission_deg',40),no_hyperextension=rep['min_F_deg']>=limits['minimum_fold_deg'],
            downstroke_fold=rep['max_F_downstroke_deg']<=limits['downstroke_max_deg'],
            core_downstroke_straightness=rep['max_F_core_downstroke_deg']<=limits['core_downstroke_max_deg'],
            peak_fold=limits['peak_fold_min_deg']<=rep['max_F_deg']<=limits['maximum_fold_deg'],
            shoulder_target_fit=rep['rms_alpha_deg']<=limits['shoulder_rms_max_deg'],
            upstroke_target_fit=rep['rms_F_upstroke_deg']<=limits['fold_upstroke_rms_max_deg'])
        rep['min_alpha_deg']=float(np.degrees(alpha.min()));rep['max_alpha_deg']=float(np.degrees(alpha.max()))
        checks['peak_near_mid_upstroke']=240<=rep['peak_fold_theta_deg']<=300
        checks['shoulder_extrema']=limits['shoulder_min_range_deg'][0]<=rep['min_alpha_deg']<=limits['shoulder_min_range_deg'][1] and limits['shoulder_max_range_deg'][0]<=rep['max_alpha_deg']<=limits['shoulder_max_range_deg'][1]
        rep['target_provenance']=cfg['motion_targets'];rep['acceptance']=limits
        rep['downstroke_requirement']='Bent downstroke, replacing previous straight-wing requirement'
    if kind=='compact':checks['second_loop_Grashof']=grashof_crank_rocker(a2,L,h,model.L_IN)
    rep.update(checks={k:bool(v) for k,v in checks.items()},failed_checks=[k for k,v in checks.items() if not v],passes=bool(all(checks.values())))
    return rep


def hardware(cfg,geom,kind,params):
    """Geometry-derived mounting checks. These do not verify purchased material strength."""
    minimum_web=1e9;minimum_mesh=1e9;mesh=[]
    for gear in ([BUILD['gear'],cfg['gear']] if kind=='compact' else [cfg['gear']]):
        m,z=gear['module_mm'],gear['teeth'];a=np.radians(gear['pressure_angle_deg']);rp=m*z/2;rb=rp*np.cos(a);ra=rp+m
        ratio=(2*np.sqrt(ra*ra-rb*rb)-2*rp*np.sin(a))/(np.pi*m*np.cos(a))
        mesh.append({'teeth':z,'module_mm':m,'nominal_contact_ratio':float(ratio),'no_standard_undercut':bool(z>=2/np.sin(a)**2)})
        minimum_mesh=min(minimum_mesh,ratio)
    ligaments=[]
    for plate in geom['plates']:
        if 'bearing_plate' not in plate['name']:continue
        c=np.array(plate['center']);half=np.array(plate['size'])/2
        for h in plate['holes']:
            gap=float(np.min(half[1:]-abs(np.array(h)[1:]-c[1:]))-plate['hole_radius'])
            ligaments.append(gap)
    if kind=='direct' and cfg.get('body_package')=='small_plywood_remote_drive':
        minimum_web=4-BUILD['pivot_hole_mm']/2
        engagement=2.5;shaft_gap=None
    elif kind=='direct':
        gear=cfg['gear'];root=gear['module_mm']*(gear['teeth']/2-1.25)
        minimum_web=root-params[5]-BUILD['pivot_hole_mm']/2
        rear_end=cfg['motor']['front_face_x_mm']+cfg['motor']['body_length_mm']+cfg['motor']['rear_shaft_mm']
        engagement=min(rear_end,cfg['rear_hub_x_mm'][1])-max(cfg['gear_plane_x_mm']-gear['face_width_mm']/2,cfg['motor']['body_length_mm'])
        shaft_gap=None
    else:
        engagement=11.5;shaft_gap=2
    checks={'gear_contact_ratio':minimum_mesh>=1.2,'no_standard_undercut':all(g['no_standard_undercut'] for g in mesh),
            'bearing_seat_edge_ligament':min(ligaments)>=2,'shaft_hub_engagement':engagement>=(2.5 if cfg.get('body_package')=='small_plywood_remote_drive' else 8),
            'drive_pin_web_ligament':minimum_web>=2}
    body=None
    if cfg.get('body_package'):
        points=[]
        labels={'crank1','crank2_direct','motor_shaft','pin_A','fastener_A','pin_D','fastener_D','nut_A','nut_D','gear_hub','clamp_crank1','clamp_crank2'}
        for name,part in geom['parts'].items():
            if name.split('/')[-1] not in labels:continue
            pad=np.array([part.get('axial_half_thickness',0),part['radius'],part['radius']])
            for key in ('p','q'):points.extend([part[key]-pad,part[key]+pad])
        for name,q in geom['panels'].items():
            if not name.startswith('body_cover/'):continue
            for v in q:points.extend([v-[cfg['body_cover']['thickness_mm']/2,0,0],v+[cfg['body_cover']['thickness_mm']/2,0,0]])
        from .compact_drive import layout
        half,O,_=layout(cfg);gear_radius=cfg['gear']['module_mm']*(cfg['gear']['teeth']/2+1)
        for m in (-1,1):
            center=np.array([cfg['gear_plane_x_mm'],m*(half+O[0]),O[1]])
            pad=np.array([cfg['gear']['face_width_mm']/2,gear_radius,gear_radius]);points.extend([(center-pad)[None,:],(center+pad)[None,:]])
        for plate in geom['plates']:
            center=np.array(plate['center']);pad=np.array(plate['size'])/2;points.extend([(center-pad)[None,:],(center+pad)[None,:]])
        ps=np.concatenate(points);size=ps.max(axis=0)-ps.min(axis=0);limits=cfg['body_requirement']
        body={'depth_mm':float(size[0]),'width_mm':float(size[1]),'height_mm':float(size[2]),
              'scope':'Crank/pin sweep, short input shafts, face; outgoing wing links and remote stand excluded.',
              'shoulder_spacing_mm':cfg['shoulder_spacing_mm'],'ground_mm':cfg['ground_mm'],
              'maximum_span_if_straight_mm':cfg['shoulder_spacing_mm']+2*sum(cfg['wing_lengths_mm'].values())}
        checks['body_width']=size[1]<=limits['max_width_mm']+1e-6
        checks['body_height']=size[2]<=limits['max_height_mm']+1e-6
        checks['body_depth']=size[0]<=limits['max_depth_mm']+1e-6
    checks={k:bool(v) for k,v in checks.items()}
    return {'body_envelope':body,'checks':checks,'passes':bool(all(checks.values())),'gear_geometry':mesh,
            'minimum_bearing_seat_ligament_mm':min(ligaments),
            'rear_hub_engagement_mm':float(engagement),'motor_extension_shaft_gap_mm':shaft_gap,
            'drive_pin_web_ligament_mm':float(minimum_web) if kind=='direct' else None,
            'verified_with_purchased_hardware':False}
