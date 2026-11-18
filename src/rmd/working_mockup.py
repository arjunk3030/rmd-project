"""Two-wing split-face presentation concept; input motion is never re-synthesized."""
import json
import re
import math
import numpy as np
from .config import CONFIG_DIR, OUTPUT_DIR
from .build_viewer import write_viewer
from .assembly import gear_outline


def build():
    source = (OUTPUT_DIR / 'direct_3d.html').read_text()
    match = re.search(r'const DATA=(.*),META=(.*),DIMS=(.*),AUDIT=(.*);\n', source)
    frames, meta, _, audit = map(json.loads, match.groups())
    cfg = json.loads((CONFIG_DIR / 'presentation/mockup.json').read_text())
    wall_thickness = 4.0
    wall_gap = cfg['wall_inner_gap_mm']
    if wall_gap <= 0:
        raise ValueError('wall_inner_gap_mm must be positive')
    wall_center = (wall_gap + wall_thickness) / 2
    cfg.update(two_wings=True, split_face=True, support_planes_x_mm=[-wall_center, wall_center])
    cfg['l_link_reference'] = json.loads((CONFIG_DIR / 'presentation/l_link_reference.json').read_text())
    cfg['gear_stack'] = {'wing_teeth':56, 'motor_teeth':16,
                         'module_mm':1, 'gear_width_mm':cfg['gear_face_width_mm'], 'motor_size_mm':[24,20,20]}
    # Narrow the two wing input axes to 56 mm for direct wing-gear meshing.
    planes = {'crank1':-20, 'coupler1':-40, 'rocker1':-34, 'inner_spar':-34,
              'crank2_direct':20, 'rod2_direct':40, 'elbow_horn':34, 'outer_spar':34}
    for frame in frames:
        for part in frame['parts']:
            side, _, name = part['name'].partition('/')
            if side not in ('R', 'L'):
                continue
            if name == 'outer_spar':
                # The supplied L has a 150 mm wingtip arm; the frozen design uses 187.5 mm.
                for axis in (1, 2):
                    part['q'][axis] = part['p'][axis] + (part['q'][axis] - part['p'][axis]) * (150 / 187.5)
            shift = 11 if side == 'R' else -11
            for end in ('p', 'q'):
                part[end][1] += shift
                if name in planes:
                    part[end][0] = planes[name]
        frame.update(gears=[], panels={}, panel_variants={'tapered':{}, 'rectangular':{}},
                     rib_variants={'tapered':{}, 'rectangular':{}}, rigid_faces=[])
        p = {part['name']:part for part in frame['parts']}
        right = p['R/crank1']['p']; left = p['L/crank1']['p']; z = right[2]
        # Motor pinion above and inboard of the right wing gear.
        beta = math.radians(120)
        motor = [0, right[1]+36*math.cos(beta), z+36*math.sin(beta)]
        def mesh(phase, za, zb, a, b):
            beta=math.atan2(b[2]-a[2],b[1]-a[1])
            return beta+math.pi-math.pi/zb-(za/zb)*(phase-beta)
        angle=math.radians(frame['theta_deg'])
        op=[0,right[1],right[2]]; ol=[0,left[1],left[2]]
        pl=mesh(angle,56,56,op,ol); pm=mesh(angle,56,16,op,motor)
        frame['gears']=[{'name':name,'center':center,'phase':phase,'mirror':1,'profile':profile,'face_width_mm':cfg['gear_face_width_mm']}
                        for name,center,phase,profile in [('R/wing_gear',op,angle,'mockup56'),
                        ('L/wing_gear',ol,pl,'mockup56'),('motor_pinion',motor,pm,'mockup16')]]
    meta.update(name='Two-wing split-face mockup', mockup=True, split_mockup=True,
                mockup_bridge=False, mockup_settings=cfg, description='', files_folder='working_mockup/',
                scene_radius=250, view_center_y=0, boxes=[], plates=[], covers=[], scale_reference=False)
    for teeth in (16,56):
        meta['gear_profiles'][f'mockup{teeth}']=gear_outline(0,gear={'module_mm':1,'teeth':teeth,'pressure_angle_deg':20,'tooth_thinning_mm':0.2}).tolist()
    motor_center=frames[0]['gears'][-1]['center']
    # The motor body is stood off beyond the outer rod plane to clear the crank.
    meta['boxes']=[{'name':'motor_placeholder','center':[57,motor_center[1],motor_center[2]],'size':[24,20,20]}]
    # Conservative sampled screen: 6 mm pivot shafts against unrelated 18 mm blue bars.
    collisions={}
    for frame in frames:
        parts={p['name']:p for p in frame['parts']}
        for shaft_side in ('R','L'):
            def pt(name,end): return parts[shaft_side+'/'+name][end]
            joints={'O':(pt('crank1','p'),(-36.85,36.85)), 'A':(pt('crank1','q'),(-47.85,-12.15)),
                    'B':(pt('rocker1','q'),(-47.85,-26.15)), 'S':(pt('rocker1','p'),(min(-34,-wall_center)-7.85,max(-34,wall_center)+7.85)),
                    'D':(pt('crank2_direct','q'),(12.15,47.85)), 'E':(pt('inner_spar','q'),(-46.85,41.85)),
                    'Q':(pt('elbow_horn','q'),(26.15,47.85))}
            for bar_side in ('R','L'):
                for bar,links in [('crank1',{'O','A'}),('coupler1',{'A','B'}),('crank2_direct',{'O','D'}),('rod2_direct',{'D','Q'})]:
                    part=parts[bar_side+'/'+bar];a=np.array(part['p']);b=np.array(part['q']);axis=b[1:]-a[1:];den=float(axis@axis)
                    for joint,(p,(lo,hi)) in joints.items():
                        if shaft_side==bar_side and joint in links:continue
                        if hi<a[0]-1.85 or lo>a[0]+1.85:continue
                        u=max(0,min(1,float((np.array(p[1:])-a[1:])@axis/den)))
                        dist=float(np.linalg.norm(np.array(p[1:])-(a[1:]+u*axis)))
                        if dist<12:
                            key=f'{shaft_side}/{joint} shaft vs {bar_side}/{bar}';gap=dist-12
                            if key not in collisions or gap<collisions[key]['gap_mm']:
                                collisions[key]={'parts':key,'gap_mm':round(gap,3),'theta_deg':frame['theta_deg']}
    report={'scope':'Sampled 6 mm shaft vs 18 mm blue-bar centerline envelopes only; no triangle, L, collars, supports, gears, motor or continuous-motion collision audit.',
            'samples':len(frames),'status':'FAIL' if collisions else 'NO CONFLICTS IN LIMITED SCREEN',
            'conflicts':list(collisions.values()),'build_ready':False}
    dims = {'Linkage':'1.25× saved pivots; triangle STL differs', 'L STL':'150 mm arm as supplied (target 187.5 mm)', 'Shaft diameter':'6 mm throughout',
            'Input shaft spacing':'56 mm (concept)', 'Input shaft length':'73.7 mm (illustrative)', 'Gear face width':f"{cfg['gear_face_width_mm']:g} mm",
            'Collars':'Two: 20 mm OD × 6 mm bore × 8 mm wide', 'Drive':'16T motor pinion and two 56T wing gears',
            'Drive status':'Concept; motor, fasteners and full clearance unverified'}
    write_viewer(frames, meta, dims, audit, OUTPUT_DIR / 'working_mockup_3d.html')
    out = OUTPUT_DIR / 'working_mockup'
    out.mkdir(exist_ok=True)
    (out / 'shaft_bar_screen.json').write_text(json.dumps(report,indent=2)+'\n')
    from .spacer_schedule import write_schedule
    write_schedule(cfg, planes, out / 'spacers.md')
    (out / 'build_notes.md').write_text('''# Two-wing split-face mockup concept

The 1.25-scale saved pivot motion is unchanged; the animated outer arm is 150 mm
to match L Linkage (5).stl, not the 187.5 mm design target. The supplied triangle
STL has different pivot spacings and is NOT represented: its three distances are
approximately 34.36, 116.91 and 133.32 mm, versus the 1.25× triangle's 30.97,
116.59 and 125.00 mm. Both wings have separate O shafts;
their centers are 56 mm apart to allow the wing gears to mesh directly.
Two 20 mm OD × 10 mm clamp hubs are shown per wing. Axial planes in mm:
shoulder coupler −40, triangle −34, shoulder crank −20, supports ±9.5,
elbow crank +20, outer L +34, elbow coupler +40. All pivot shafts are shown as
6 mm diameter. E has a nominal 20 mm OD × 8 mm collar on its triangle side; the other
end and the A, B, D, Q and S joints have schematic 1 mm retaining rings, not
selected parts. The input crank hubs retain the O shaft in the illustration.
Approximate drawing lengths per wing: O 73.7, A 35.7, B 21.7, S 59.2,
D 35.7, E 88.7, Q 21.7 mm. These are visualization envelopes, not cut lengths.
Each link is 3.7 mm thick. The A and D joint part faces are 16.3 mm apart,
and B and Q faces are 2.3 mm apart; these joints need actual inner-race spacers.
The E parts are 64.3 mm apart, so the long shaft needs a supported carrier or
revised packaging. The 10 mm long crank hubs end only 0.3 mm from the adjacent
triangle/L planes; tolerances, clamp ears and hardware make that a serious
assembly concern. Sleeves, washers, collars and support of these stacks have
not been designed in CAD. The simplified shaft/bar check is in
shaft_bar_screen.json and does not include those features.

This is NOT clearance-validated or fabrication-ready. In particular, the chosen
20 mm hubs, ears, clamp screws, enlarged links, supports, collars, shafts and
motor have not had a full moving-solid collision, retention or load check.
The L is drawn from the supplied L Linkage (5).stl face outline; its E–Q pivot
spacing already matches the 1.25× design and E–T is 150 mm in the file. No
stretching is applied to the L outline or bearing holes.
The clamp is a simplified representation of the supplied coupler STL, not its
exact mesh. The STL appears to use meters while the L file uses millimeters.
An illustrative 16T motor pinion drives a 56T wing gear that meshes directly
with the other 56T wing gear. At module 1, the 56 mm O–O pitch layout reverses
the wing shafts; motor to wing ratio is 56:16 = 3.5:1. Teeth are illustrative profiles.
The nominal 29 mm gear tip radius leaves 3 mm from the 6 mm shoulder shaft,
because O–S is 35 mm. Actual teeth, tolerances and
shaft hardware need a full clearance check. Gear backlash, printing accuracy,
gears' attachment, idler loading, motor mount, motor
shaft extension, support holes and all moving-solid clearances are unverified.
The motor is a 24 × 20 × 20 mm placeholder, not a selected gearmotor. Its body
starts at x=45 mm on a long motor-shaft extension; the required standoff bracket,
shaft support and coupling are not designed. Two
20 mm OD × 8 mm collars are at the E pivots. The
previous placement of the larger elbow collar on the opposite end intersected
the elbow coupler and was not retained. Full assembly remains unverified.
Shaft collars must be selected with a 6 mm bore and dimensioned with actual
hardware and retention. The 88.7 mm E shaft is an unsupported-length concern.
''')
    with (out / 'build_notes.md').open('a') as notes:
        notes.write(f"\nGear width is {cfg['gear_face_width_mm']:.2f} mm and the wall inside gap is {wall_gap:.2f} mm. "
                    f"With gears centered, nominal gear-face to wall-face gap is {(wall_gap-cfg['gear_face_width_mm'])/2:.2f} mm per side. "
                    "This is not a spacer length or proof that gear hubs, shaft stops and bearing races fit.\n")
    (out / 'shaft_schedule.md').write_text('''# Preliminary shaft and spacer schedule

All lengths below describe the current visual envelope in mm, not approved cut
lengths. Each wing uses one of each. Actual collars, grooves, washers, bearing
seats, shaft locking, gear hubs, fits and supports are not finalized. Do not cut
to these values until the CAD assembly and hardware have been checked.

| Joint | Visual shaft length | Illustrated retention | Unresolved stack |
|---|---:|---|---|
| O input | 73.7 | Two fixed crank hubs | Gear hub locking, motor/gear drive and end retention. |
| A | 35.7 | Two schematic thin rings | About 16.3 between link faces; bearing protrusion and race spacers unresolved. |
| B | 21.7 | Two schematic thin rings | About 2.3 between link faces; bearing protrusion and race spacers unresolved. |
| S | 59.2 | Two schematic thin rings | Supports and shoulder piece must be located, and fixed/rotating bearing races resolved. |
| D | 35.7 | Two schematic thin rings | About 16.3 between link faces; bearing protrusion and race spacers unresolved. |
| E elbow | 88.7 | One 20 OD × 8 wide collar, one schematic thin ring | 64.3 between link faces; needs a supported carrier and separately designed race spacers. |
| Q | 21.7 | Two schematic thin rings | About 2.3 between link faces; bearing protrusion and race spacers unresolved. |

No idler shafts are required in the three-gear concept. The motor
shaft and coupling cannot be dimensioned until an actual motor is selected.
The gap values are between nominal 3.7 mm part faces, not spacer cut lengths:
the 3 mm bearings, their seating depths and contact surfaces must be known first.
Retaining-ring dimensions and groove geometry are placeholders; use a real
6 mm shaft retainer specification. Confirm collar and bearing clearances.
''')
    print('Wrote two-wing mockup concept; drive and full physical clearances unverified.')
