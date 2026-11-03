"""Reproducible limited check of spacer-only alternatives; no refit or adoption."""
import json,numpy as np,itertools
from rmd.direct_drive import Problem,settings
from rmd.designs import get_direct
from rmd.single_face import geometry
from rmd.clearance import segment_distance
from rmd.config import CONFIG_DIR


def generate(out):
    v,ba,be,_=get_direct(allow_fit=False);p=Problem(1440);sim=p.state(v,ba,be)['simulation'];base=settings();base.update(json.loads((CONFIG_DIR/'single_face.json').read_text()))
    results=[]
    for ra,rd in [(-37,-46),(-52,-37),(-58,-46),(-46,-37),(-37,-23),(-46,-23)]:
     cfg=dict(base,front_rod_plane_x_mm=ra,rear_rod_plane_x_mm=rd);g=geometry(sim,cfg)
     ps={n:q for n,q in g['parts'].items() if n.startswith('R/') and not any(x in n for x in ['finger','clamp','hub'])};bad=[]
     for (n,a),(m,b) in itertools.combinations(ps.items(),2):
      if a['joints']&b['joints']:continue
      def ext(x):
       h=x.get('axial_half_thickness',0) if np.allclose(x['p'][:,0],x['q'][:,0]) else 0
       return np.minimum(x['p'][:,0],x['q'][:,0])-h,np.maximum(x['p'][:,0],x['q'][:,0])+h
      a0,a1=ext(a);b0,b1=ext(b);ax=np.maximum(a0-b1,b0-a1)
      def flat(q):q=q.copy();q[:,0]=0;return q
      rad=segment_distance(flat(a['p']),flat(a['q']),flat(b['p']),flat(b['q']))-a['radius']-b['radius'];gap=np.where((ax>0)|(rad>0),np.hypot(np.maximum(ax,0),np.maximum(rad,0)),np.maximum(ax,rad));k=gap.argmin()
      if gap[k]<1:bad.append((n,m,round(float(gap[k]),2)))
     results.append({'shoulder_coupler_plane_mm':ra,'elbow_coupler_plane_mm':rd,'conflicts':[{'parts':[n,m],'gap_mm':gap} for n,m,gap in bad]})
    
    (out/'layer_checks.json').write_text(json.dumps({'scope':'Limited original 3 mm link/pin envelopes for one wing; excludes printed triangle interiors, bosses, hubs, frame and actuator. Negative gap means overlap. Not a full mock-up audit.','samples':1440,'required_gap_mm':1,'results':results},indent=2)+'\n')


def critical_collision(settings):
    """Detect a definite intersection of the shown A–B link and D screw.

    The rectangular center section of the printed A–B link is 8 mm wide;
    this check uses that section only, so rounded bosses cannot make the
    detected collision disappear. End-on and material fits are not audited.
    """
    v, ba, be, _ = get_direct(allow_fit=False)
    problem = Problem(1440)
    sim = problem.state(v, ba, be)['simulation']
    a, b, d = sim['A1'], sim['B1'], sim['P2']
    ab = b - a
    t = np.clip(np.sum((d-a)*ab, axis=1) / np.sum(ab*ab, axis=1), 0, 1)
    distance = np.linalg.norm(d-(a+t[:, None]*ab), axis=1)
    # Restrict to the rectangular middle of the link, avoiding end-cap assumptions.
    valid = (t > 0) & (t < 1)
    threshold = (settings['link_width_mm'] + settings['screw_diameter_mm']) / 2
    hit = valid & (distance < threshold)
    k = int(np.argmin(np.where(valid, distance, np.inf)))
    return {'status': 'FAIL' if np.any(hit) else 'UNVERIFIED',
            'parts': ['shoulder coupler A–B', 'elbow crank screw D'],
            'samples': len(distance), 'worst_input_deg': float(np.degrees(problem.theta[k])),
            'planar_center_distance_mm': float(distance[k]),
            'intersection_threshold_mm': float(threshold),
            'affected_samples': int(np.count_nonzero(hit)),
            'scope': 'A–B middle section against D screw only; original axial stack places D through the A–B layer. This does not check other parts, the actual fastener selection, or continuous-time clearance.'}


def support_clearance(mock):
    """Screen the moved plate against E/Q nuts and report axial stack gaps.

    All other moving printed bodies stop before the plate in the depicted
    depth arrangement. This remains a limited sampled envelope test.
    """
    v, ba, be, _ = get_direct(allow_fit=False)
    problem = Problem(1440)
    sim = problem.state(v, ba, be)['simulation']
    cfg = settings(); cfg.update(json.loads((CONFIG_DIR/'single_face.json').read_text()))
    g = geometry(sim, cfg)['parts']
    O, S = g['R/crank1']['p'][0, 1:], g['R/rocker1']['p'][0, 1:]
    center = (O+S)/2
    half = np.array([18.,29.])
    radius = mock['nut_across_flats_mm']/np.sqrt(3)
    gaps = {}
    for label, point in [('E',g['R/inner_spar']['q'][:,1:]),('Q',g['R/elbow_horn']['q'][:,1:])]:
        distance = np.linalg.norm(np.maximum(np.abs(point-center)-half,0),axis=1)
        gaps[label] = float(distance.min()-radius)
    plate_rear = mock['support_plane_x_mm']-2
    outer_front = cfg['wing_plane_x_mm']+4.5+mock['plate_thickness_mm']/2
    return {'samples':1440,'plate_x_interval_mm':[plate_rear,mock['support_plane_x_mm']+2],
            'motor_front_x_mm':mock['motor_front_x_mm'],
            'outer_print_to_plate_axial_gap_mm':float(plate_rear-outer_front),
            'E_Q_nut_to_plate_conservative_gaps_mm':gaps,
            'scope':'Moving plate envelope and E/Q nut to support plate only; does not validate all parts, shaft fits, hardware, motor mounting, strength, or the known A–B/D collision.'}


def offset_bridge_screen(bridge_mm=20, step_mm=9.5):
    """Screen the two axial bridge legs against the elbow coupler, 1,440 poses."""
    v, ba, be, _ = get_direct(allow_fit=False)
    problem = Problem(1440)
    sim = problem.state(v, ba, be)['simulation']
    a, b, d, q = (sim[key] for key in ('A1', 'B1', 'P2', 'Q2'))
    direction = (b-a)/np.linalg.norm(b-a, axis=1)[:,None]
    zeros = np.zeros((len(a),1))
    lift = lambda v: np.concatenate((zeros,v),axis=1)
    result=[]
    for name, point in [('A',a+step_mm*direction),('B',b-step_mm*direction)]:
        distance=segment_distance(lift(point),lift(point),lift(d),lift(q))
        k=int(distance.argmin())
        result.append({'bridge_leg':name,'min_centerline_distance_mm':float(distance[k]),
                       'input_angle_deg':float(np.degrees(problem.theta[k])),
                       'combined_half_width_mm':8.0,'intersects':bool(distance[k]<8)})
    # The short portions remaining in the original layer can also hit D.
    for name, begin, end in [('A',a,a+step_mm*direction),('B',b-step_mm*direction,b)]:
        distance=segment_distance(lift(begin),lift(end),lift(d),lift(d))
        k=int(distance.argmin())
        result.append({'front_section':name,'min_centerline_distance_mm':float(distance[k]),
                       'input_angle_deg':float(np.degrees(problem.theta[k])),
                       'combined_half_width_mm':5.5,'intersects':bool(distance[k]<5.5)})
    return {'status':'FAIL' if any(r['intersects'] for r in result) else 'UNVERIFIED',
            'bridge_offset_mm':bridge_mm,'step_from_joint_mm':step_mm,'samples':1440,
            'explanation':'The 8 mm wide bridge legs cross the elbow coupler; the end sections also cross the D screw. This is a limited sampled screen, not a complete collision audit.',
            'results':result}
