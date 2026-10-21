"""Alternative axial package: common V-crank, both drives on the front face.
Run: python3 -m rmd.single_face (with PYTHONPATH=src).
Preserves the original synthesis and checks the new physical arrangement.
"""
import json
import numpy as np
from . import direct_drive as direct, direct_package, compact_drive as compact
from .designs import get_direct
from .design_io import load_design
from .config import OUTPUT_DIR,CONFIG_DIR
from .frames3d import make_frames
from .build_viewer import write_viewer
from . import checks


def geometry(sim,cfg):
    g=direct_package.geometry(sim,cfg)
    for side in ('R','L'):
        p=g['parts'];prefix=side+'/'
        # One common crank hub replaces two clamps; both arms are one V-shaped part.
        p.pop(prefix+'clamp_crank2')
        for shaft,start in [('motor_shaft',cfg['front_crank_plane_x_mm']-2),('shoulder_shaft',cfg['front_rocker_plane_x_mm']-2)]:
            p[prefix+shaft]['p'][:,0]=start;p[prefix+shaft]['q'][:,0]=12
    return g


def build():
    cfg=direct.settings();cfg.update(json.loads((CONFIG_DIR/'single_face.json').read_text()))
    cfg['body_cover']=dict(cfg['body_cover'],enabled=False)
    v,ba,be,saved=get_direct(allow_fit=False);d,b1,b2,_=load_design()
    def sim(theta):
        p=direct.Problem(len(theta));p.theta=np.asarray(theta)
        from .direct_targets import curves
        p.target['alpha'],p.target['F']=curves(p.theta,p.cfg)
        return p.state(v,ba,be)['simulation']
    audit=compact.audit(d,b1,b2,cfg,geometry_fn=lambda d,s,c:geometry(sim(s['thetas']),c),gear_specs_fn=direct.gears)
    th=np.linspace(0,2*np.pi,cfg['audit_samples'],endpoint=False);s=sim(th)
    motion=checks.motion(s,'direct',v,d,cfg,sim)
    report={'name':'Single-face Stephenson option','status':audit['status'],'kinematics':motion,'clearance':audit,'build_ready':False,
            'scope':'Alternative axial packaging, same solved motion. No load qualification for longer cantilever shafts; V-crank web and fastener manufacture require detail design.'}
    out=OUTPUT_DIR/'single_face';out.mkdir(exist_ok=True)
    (out/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    (out/'layout.json').write_text(json.dumps(cfg,indent=2)+'\n')
    th=np.radians(np.arange(0,360,5));s=sim(th);g=geometry(s,cfg)
    placement=lambda p,side:compact.transform(p,side,cfg)+[cfg['wing_plane_x_mm']+(cfg['left_layer_spread_mm'] if side=='L' else 0),0,0]
    frames,meta=make_frames(s,g,cfg,direct.gears,placement,name='Single-face Stephenson option',design_id='direct',description='Both drives sit on the front face. Each wing uses one V-shaped crank with two pin locations and one rigid rocker/inner-wing assembly. Rods remain in separated plywood layers. Same motion as the original. EXPERIMENT: the shoulder rod collides with the elbow crank pin during the cycle. Shaded triangles indicate rigid bodies, not additional manufactured plates. This option is not suitable for fabrication as shown.')
    meta.update(other_viewer='direct_3d.html',files_folder='single_face/',integrated_crank=True)
    for f in frames:
        p={part['name']:part for part in f['parts']}
        f['rigid_faces']=[]
        for side in ('R','L'):
            def endpoint(name,key):return p[side+'/'+name][key]
            f['rigid_faces'].extend([{'points':[endpoint('crank1','p'),endpoint('crank1','q'),endpoint('crank2_direct','q')],'color':'rgba(67,139,255,.28)'},{'points':[endpoint('rocker1','p'),endpoint('rocker1','q'),endpoint('inner_spar','q')],'color':'rgba(23,190,207,.15)'}])
    write_viewer(frames,meta,{'Crank plane':str(cfg['front_crank_plane_x_mm'])+' mm','Rod A / elbow planes':str([cfg['front_rod_plane_x_mm'],cfg['rear_rod_plane_x_mm']])+' mm','Minimum transmission':f"{motion['mu1_min_deg']:.2f}° / {motion['mu2_min_deg']:.2f}°"},report,OUTPUT_DIR/'single_face_3d.html')
    (out/'build_notes.md').write_text('# Single-face Stephenson option\n\n'+report['scope']+'\n\nNominal clearance: '+audit['status']+'. Conflicts: '+str(audit['conflict_count'])+'.\n\nBoth crank arms are coplanar and fixed to a single hub: fabricate as one V-shaped crank. The two connecting rods need separate layers; this is not a completely coplanar construction. The rocker and inner spar also share one plane and form one rigid assembly. Original synthesized lengths and mounting angles are unchanged. **Known failure: the shoulder rod crosses the extended elbow crank pin D on each wing. Do not fabricate this arrangement as shown.** Placing the elbow rod on the inside instead causes interference with the shaft or shoulder joint. Small axial-spacing changes alone do not resolve these observed conflicts; a different crank/pin support arrangement, spatial bracket design, or re-synthesis is needed. The stand, belt and reversing gears remain. Longer overhung shafts require a new load/deflection check before fabrication.\n')
    print(json.dumps({'status':audit['status'],'conflicts':audit['conflicts']},indent=2))
    return report

if __name__=='__main__':build()
