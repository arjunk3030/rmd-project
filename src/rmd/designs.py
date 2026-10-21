"""The two supported compact designs and their complete build/validation pipeline."""
import hashlib
import json
from pathlib import Path
import numpy as np
from .config import CONFIG_DIR,OUTPUT_DIR,input_snapshot
from .design_io import load_design
from . import model,compact_drive as compact,direct_drive as direct
from . import checks,loads
from .frames3d import make_frames
from .build_viewer import write_viewer


def direct_digest():
    _,_,_,reference=load_design()
    payload={'common':input_snapshot(),'layout':direct.settings(),
             'seed':json.loads((CONFIG_DIR/'direct_seed.json').read_text()),
             'reference':reference['optimized_design_deg_mm'],'branches':reference['assembly_branch'],
             'algorithm':hashlib.sha256(Path(direct.__file__).read_bytes()).hexdigest(),
             'package_algorithm':hashlib.sha256((Path(direct.__file__).parent/'direct_package.py').read_bytes()).hexdigest(),
             'target_algorithm':hashlib.sha256((Path(direct.__file__).parent/'direct_targets.py').read_bytes()).hexdigest()}
    return hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest(),payload


def get_direct(refit=False,allow_fit=True):
    path=OUTPUT_DIR/'direct/dimensions.json';digest,inputs=direct_digest()
    if path.exists() and not refit:
        data=json.loads(path.read_text())
        if data.get('input_digest')==digest:return np.array(data['parameters']),data['branchA'],data['branchE'],data
    if not allow_fit:raise ValueError('Saved direct fit does not match these inputs. Use the explicit redesign workflow to synthesize a new candidate.')
    print('Synthesizing direct six-bar (joint full-cycle fit)...',flush=True)
    v,ba,be=direct.fit();data={'design':'direct','input_digest':digest,'inputs':inputs,
        'parameter_names':direct.settings()['parameter_names'],'parameters':v.tolist(),'branchA':ba,'branchE':be,
        'units':'length mm; angles radians','method':direct.settings()['synthesis_method'],
        'provenance':'Numerically synthesized outputs, not measured dimensions.'}
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,indent=2)+'\n')
    return v,ba,be,data


def build(kind,*,refit=False,video=False,validate_only=False,allow_fit=True):
    d,b1,b2,saved=load_design();params=None
    if kind=='compact':
        cfg=compact.settings();name=cfg['name'];gear_fn=compact.gear_specs
        def simulation(theta):return model.simulate(d,theta,b1,b2)
        def geometry_fn(theta):return compact.geometry(d,simulation(theta),cfg)
        packet={'design':'compact','reference':saved,'package_inputs':cfg,
                'method':cfg['synthesis_method'],'provenance':'Synthesized reference lengths; derived rigid placement rotation.'}
        desc='One motor and one reversing gear pair drive both wings. Each O input also drives an S elbow crank through a local 50T pair. Six gears total. A moves the inner wing; B uses the moving inner wing as its reference.'
        placement=lambda p,side:compact.transform(p,side,cfg)
    else:
        cfg=direct.settings();name=cfg['name'];gear_fn=direct.gears
        params,ba,be,packet=get_direct(refit,allow_fit)
        def simulation(theta):return geometry_fn(theta)['simulation']
        def geometry_fn(theta):return direct.geometry(params,ba,be,theta)
        desc=''
        placement=lambda p,side:compact.transform(p,side,cfg)+np.array([cfg['wing_plane_x_mm']+(cfg.get('left_layer_spread_mm',0) if side=='L' else 0),0,0])
    theta=np.linspace(0,2*np.pi,cfg['audit_samples'],endpoint=False)
    geom=geometry_fn(theta);sim=geom.get('simulation')
    if sim is None:sim=simulation(theta)
    layout=compact.audit(d,b1,b2,cfg,geometry_fn=lambda d,s,c:geometry_fn(s['thetas']),gear_specs_fn=gear_fn)
    kinematic=checks.motion(sim,kind,params,d,cfg,simulation)
    hardware=checks.hardware(cfg,geom,kind,params);load=loads.estimate(sim,geom,kind,cfg)
    if kind=='direct':
        layout['links_mm']={'a1':params[0],'b1':params[1],'c1':params[2],'a2':params[5],'horn':params[7],'rod':params[9]}
        layout['rocker_mounting_offset_deg']=float(np.degrees(params[3]))
    passed=kinematic['passes'] and layout['prototype_layout_passes'] and hardware['passes'] and all(load['conditional_strength_checks'].values())
    report={'design':kind,'name':name,'status':'PASS' if passed else 'FAIL','kinematics':kinematic,
            'clearance':layout,'hardware':hardware,'loads':load,'nominal_prototype_passes':bool(passed),
            'build_ready':False,
            'meaning':'PASS is the nominal sampled mechanism and assumed-load envelope. Fits, material properties, dynamic motor torque, retention and loaded operation remain unverified.'}
    out=OUTPUT_DIR/('compact' if kind=='compact' else 'direct');out.mkdir(parents=True,exist_ok=True)
    (out/'validation.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    (out/'load_estimate.json').write_text(json.dumps(load,indent=2,allow_nan=False)+'\n')
    if kind=='compact':
        # Actual installed kappa/phase differ from canonical reference coordinates.
        _,O,rho=compact.layout(cfg)
        packet.update(input_snapshot=input_snapshot(),installed={'O_local_mm':O.tolist(),'kappa_deg':float(np.degrees(d['kappa1']+rho)),
            'input_crank_phase_deg':float(np.degrees(rho)),'shoulder_spacing_mm':cfg['shoulder_spacing_mm']})
        (out/'dimensions.json').write_text(json.dumps(packet,indent=2)+'\n')
    print(f"{name}: {report['status']} | mu {kinematic['mu1_min_deg']:.2f}° / {kinematic['mu2_min_deg']:.2f}° | fold {kinematic['max_F_deg']:.2f}° | {layout['conflict_count']} conflicts",flush=True)
    if not passed:print('Failed motion checks:',kinematic['failed_checks'],'; hardware:',hardware['checks'],'; conflicts:',layout['conflicts'],flush=True)
    if validate_only:return report
    th=np.radians(np.arange(0,360,5.));g=geometry_fn(th);s=g.get('simulation')
    if s is None:s=simulation(th)
    frames,meta=make_frames(s,g,cfg,gear_fn,placement,name=name,design_id=kind,description=desc)
    dims={'Shoulders (chosen)':f"{cfg['shoulder_spacing_mm']:.1f} mm",'Gear count':str(layout['gear_count']),
          'A crank / rod / rocker':f"{layout['links_mm']['a1']:.2f} / {layout['links_mm']['b1']:.2f} / {layout['links_mm']['c1']:.2f} mm",
          'Transmission minimum A / elbow':f"{kinematic['mu1_min_deg']:.2f}° / {kinematic['mu2_min_deg']:.2f}°",
          'Maximum fold':f"{kinematic['max_F_deg']:.2f}°",'Moving-part envelope gap':f"{layout['minimum_nonadjacent_part_clearance_mm']:.2f} mm",
          'Estimated running torque target':f"{load['required_running_torque_target_Nm']:.3f} Nm"}
    write_viewer(frames,meta,dims,report,OUTPUT_DIR/(kind+'_3d.html'))
    from .exports import export
    export(kind,frames,meta,cfg,report,packet,g,params)
    if video:
        from .animate3d import video as make_video
        make_video(frames,meta,out)
    return report
