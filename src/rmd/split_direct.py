"""One-wing split-face concept, using the saved direct design without refitting."""
import json
import re
import numpy as np
from .config import CONFIG_DIR,OUTPUT_DIR
from .build_viewer import write_viewer
from .designs import get_direct
from .direct_drive import Problem
from .clearance import point_triangle_distance


def build():
    source=OUTPUT_DIR/'direct_3d.html'
    if not source.exists():raise ValueError('Generate the saved direct viewer first: python3 run_all.py demo')
    match=re.search(r'const DATA=(.*),META=(.*),DIMS=(.*),AUDIT=(.*);\n',source.read_text())
    frames,meta,_,audit=map(json.loads,match.groups())
    cfg=json.loads((CONFIG_DIR/'presentation/mockup.json').read_text())
    cfg.update(split_face=True,support_planes_x_mm=[-9.5,9.5])
    ref={p['name']:p for p in frames[0]['parts']};O=ref['R/crank1']['p'];S=ref['R/rocker1']['p']
    meta.update(name='One wing · split-face direct drive',mockup=True,split_mockup=True,mockup_bridge=False,
                mockup_settings=cfg,description='',files_folder='split_direct/',other_viewer='direct_3d.html',
                scene_radius=170,view_center_y=S[1]+90,boxes=[],plates=[],covers=[])
    for fr in frames:
        fr['parts']=[p for p in fr['parts'] if p['name'].startswith('R/')]
        for part in fr['parts']:
            if part['name']=='R/inner_spar':part['p'][0]=part['q'][0]=-22
            if part['name'] in ('R/elbow_horn','R/outer_spar'):part['p'][0]=part['q'][0]=18.5
            if part['name']=='R/motor_shaft':part['p'][0],part['q'][0]=-18,19
        fr.update(gears=[],panels={},panel_variants={'tapered':{},'rectangular':{}},rib_variants={'tapered':{},'rectangular':{}},rigid_faces=[])
    v,ba,be,_=get_direct(allow_fit=False);p=Problem(1440);sim=p.state(v,ba,be)['simulation']
    lift=lambda a:np.column_stack((np.zeros(len(a)),a))
    a,b,e=sim['A1'],sim['B1'],sim['E'];zero=np.zeros_like(a)
    distance=point_triangle_distance(lift(a),lift(zero),lift(b),lift(e))
    # 7 mm is the max boss extent around the nominal triangle; a nut is bounded by its circumradius.
    triangle_gap=float(distance.min()-7-cfg['nut_across_flats_mm']/np.sqrt(3))
    report={'status':'UNVERIFIED','scope':'Limited 1440-pose envelope screen, not a full solid/hardware/motor audit.',
            'D_screw_to_AB_axial_gap_mm':39.5,
            'A_hardware_to_inner_triangle_conservative_gap_mm':triangle_gap,
            'motor_envelope_diameter_mm':14,'motor_envelope_length_mm':5,
            'motor_to_elbow_coupler_axial_gap_mm':1.0,
            'inner_D_trial':{'status':'FAIL','scope':'At the zero-angle pose, placing D on the A crank plane while keeping the elbow coupler outside requires the D pin to cross both support plates.', 'input_angle_deg':0, 'D_to_O_mm':float(np.linalg.norm(sim['P2'][0]-p.O)), 'D_to_S_mm':float(np.linalg.norm(sim['P2'][0]))},
            'limitations':['The 14 × 5 mm motor is an unselected envelope, not a verified actuator.', 'No full moving-solid, joint-fit, support, bearing or torque validation.']}
    out=OUTPUT_DIR/'split_direct';out.mkdir(exist_ok=True)
    (out/'clearance.json').write_text(json.dumps(report,indent=2)+'\n')
    (out/'build_notes.md').write_text('''# One-wing gearless split-face concept

The two blue crank arms lie at x = −16 and +16 mm. Their O hubs are rigidly locked to the same shaft; the 32 mm axial separation is a packaging feature, not two motors. The yellow inner-wing triangle is one printed body at x = −22 mm; its elbow pin reaches the outer wing at x = +18.5 mm. These are preliminary printed shapes, not final CAD.

The assumed gray motor envelope is only 14 mm diameter and 5 mm long, placed between the rear crank arm and elbow coupler. No motor has been selected; a motor this short with adequate output torque has not been identified. A larger motor or different mount will require a new clearance check. Grounded supports and shaft locking are schematic.

The old same-face D/A–B pin collision is separated by 39.5 mm axially in this concept. Other checks are limited to the named envelopes in clearance.json. Printed bodies, bearing retention, support attachment, operating torque and full-cycle physical clearance are NOT validated. Moving D onto the front crank face makes its long pin pass through both fixed support plates. This is not a collision-free alternative as currently drawn.
''')
    dims={'Crank-arm planes':'−16 / +16 mm','Wing triangle plane':'−22 mm','Motor envelope (unselected)':'14 mm dia × 5 mm long','D pin / A–B axial gap':'39.5 mm'}
    write_viewer(frames,meta,dims,audit,OUTPUT_DIR/'split_direct_3d.html')
    print('Wrote split-face concept; motor package and full printed-solid clearance remain unverified.')
