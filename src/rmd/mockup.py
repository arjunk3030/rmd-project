"""Separate printed-mockup appearance from saved same-face poses; no fitting."""
import json
import re
from .config import CONFIG_DIR,OUTPUT_DIR
from .build_viewer import write_viewer


def build(offset=False):
    source=OUTPUT_DIR/'single_face_3d.html'
    if not source.exists():
        from .single_face import build as same_face
        same_face()
    match=re.search(r'const DATA=(.*),META=(.*),DIMS=(.*),AUDIT=(.*);\n',source.read_text())
    frames,meta,_,audit=map(json.loads,match.groups())
    cfg=json.loads((CONFIG_DIR/'presentation/mockup.json').read_text())
    for key,value in cfg.items():
        if key.endswith('_mm') and key not in ('support_plane_x_mm','motor_front_x_mm') and value<=0:raise ValueError(f'{key} must be positive')
    if cfg['bearing_bore_mm']>=cfg['bearing_outer_diameter_mm']:raise ValueError('Bearing bore must be smaller than outside diameter')
    if offset:cfg['coupler_bridge_mm']=20
    meta.update(name='Offset coupler experiment' if offset else 'One-wing mock-up · direct input',mockup=True,mockup_bridge=offset,mockup_settings=cfg,description='',files_folder='offset_experiment/' if offset else 'mockup/',other_viewer='single_face_3d.html')
    reference={p['name']:p for p in frames[0]['parts']}
    O=reference['R/crank1']['p'];S=reference['R/rocker1']['p']
    fx=cfg['support_plane_x_mm'];front=cfg['motor_front_x_mm'];length=cfg['motor_length_mm'];face=cfg['motor_face_mm']
    meta.update(scene_radius=170,view_center_y=S[1]+90,boxes=[{'name':'direct motor envelope','center':[front+length/2,O[1],O[2]],'size':[length,face,face]}],plates=[{'name':'pivot support','center':[fx,(O[1]+S[1])/2,(O[2]+S[2])/2],'size':[4,36,58],'holes':[[fx,*O[1:]],[fx,*S[1:]]],'hole_radius':5}],covers=[])
    for fr in frames:
        fr['parts']=[p for p in fr['parts'] if p['name'].startswith('R/')]
        for part in fr['parts']:
            if part['name'] in ('R/motor_shaft','R/shoulder_shaft'):
                part['q'][0]=front
        fr['gears']=[]
        fr['panels']={};fr['panel_variants']={'tapered':{},'rectangular':{}};fr['rib_variants']={'tapered':{},'rectangular':{}};fr['rigid_faces']=[]
    dims={'Printed plate (assumed)':f"{cfg['plate_thickness_mm']} mm",'Bearing OD / bore / width (assumed)':f"{cfg['bearing_outer_diameter_mm']} / {cfg['bearing_bore_mm']} / {cfg['bearing_width_mm']} mm",'Screw diameter (assumed)':f"{cfg['screw_diameter_mm']} mm"}
    if offset:dims['Bridge offset (trial)']=f"{cfg['coupler_bridge_mm']} mm"
    out=OUTPUT_DIR/('offset_experiment' if offset else 'mockup');out.mkdir(exist_ok=True)
    (out/'settings.json').write_text(json.dumps(cfg,indent=2)+'\n')
    (out/'build_notes.md').write_text('''# One-wing mock-up

One right wing, directly driven at O. No opposite wing, gears, belt, fabric or fabric ribs. Yellow: solid inner-wing triangle and outer spar. Blue: remaining printed linkage bodies. Red, when enabled: shoulder coupler A–B. All screws, including D, are gray. Show collision pauses at 285 degrees (nearest displayed frame to the original audit's 283.5-degree worst case). Highlight identifies the pair, not a live collision sensor.

Same frozen pivot distances, phases and motion. The crank triangle and inner-wing triangle are rigid moving links, not stationary plates. Printed seats now have through-bores rather than rings drawn over solid material. The outer-wing lever and spar share their own depth plane, separated from the inner-wing triangle. Their common material is one rigid printed body. Bearing/screw/nut envelopes remain illustrative; the actuator box is a placeholder, not a selected motor. The motor front was moved to x = −4 mm and the support center to x = −6 mm, shortening the axial gap. Motor fit and loaded performance remain unverified. See motor_support_check.json for the limited support screen; the printed shapes have not received a complete clearance or load audit.

The original same-face A–B/D conflict exists within one wing, so removing the other wing does not fix it. Tested coupler-layer swaps remove that pair but create elbow-coupler collisions with A/B pins or the input shaft. See layer_checks.json for the limited 1440-pose link/pin screen. It is not a printed-triangle audit or a proof that no other layout exists. No tested alternative is adopted here.

Keeping the planar kinematics may still be possible with a specially routed offset coupler or different shaft supports. Merely swapping spacers is not a demonstrated solution. Bearing retention, inner-race spacers, screw lengths and print tolerances remain to be designed. Nuts should clamp inner races/spacers, not squeeze rotating printed faces.
''')
    from .mockup_clearance import generate, critical_collision, support_clearance, offset_bridge_screen
    generate(out)
    support=support_clearance(cfg)
    (out/'motor_support_check.json').write_text(json.dumps(support,indent=2)+'\n')
    critical=critical_collision(cfg)
    if not offset:
        (out/'critical_collision.json').write_text(json.dumps(critical,indent=2)+'\n')
    if not offset and critical['status']=='FAIL':
        print(f"CONFIRMED: A–B intersects D screw near {critical['worst_input_deg']:.2f}°; mock-up is not collision-free.")
    if offset:
        result=offset_bridge_screen(cfg['coupler_bridge_mm'])
        (out/'clearance.json').write_text(json.dumps(result,indent=2)+'\n')
        (out/'build_notes.md').write_text('# Offset coupler experiment\n\nThe red coupler steps 20 mm behind its original layer, then returns at both ends. The legs cross the elbow coupler near 103.5° and 285°, and the end sections still collide with the D screw. The 8 mm cross-section is illustrative. This candidate fails the limited clearance test; it is not buildable as shown. Original joint positions, link-center distances and motion remain unchanged.\n')
    write_viewer(frames,meta,dims,audit,OUTPUT_DIR/('offset_experiment_3d.html' if offset else 'mockup_3d.html'))
    print('Generated offset experiment: FAIL, bridge intersects D screw and elbow coupler.' if offset else 'Printed mock-up generated; hardware dimensions illustrative, clearance unverified.')
