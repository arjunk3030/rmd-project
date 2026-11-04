"""Top-mounted motor concept layered onto the frozen two-wing poses."""
from copy import deepcopy
import json
from pathlib import Path
import numpy as np
from .assembly import gear_outline
from .config import CONFIG_DIR

REMOVED={'body_pulley','pedestal_pulley','belt_span_-1','belt_span_1','drive/output_shaft','top_motor_shaft'}


def apply(frames,meta,dims):
    cfg=json.loads((CONFIG_DIR/'presentation/top_motor.json').read_text())
    frames,meta,dims=deepcopy(frames),deepcopy(meta),dict(dims)
    module=1.0;old_teeth=34;new_teeth=cfg['motor_pinion_teeth'];beta=np.radians(cfg['angle_above_right_gear_deg'])
    first=next(g for g in frames[0]['gears'] if g['name']=='R/distribution')
    x,y,z=first['center'];d=cfg['center_distance_mm'];cy=y+d*np.cos(beta);cz=z+d*np.sin(beta)
    tooth={'module_mm':module,'teeth':new_teeth,'pressure_angle_deg':20,'tooth_thinning_mm':0.1}
    meta['gear_profiles']['top_motor']=gear_outline(0,gear=tooth).tolist()
    front=cfg['motor_front_x_mm'];length=cfg['motor_length_mm'];side=cfg['motor_face_mm']
    meta['boxes']=[b for b in meta['boxes'] if b['name'] not in ('drive/actuator_reservation','top_motor')]
    meta['boxes'].append({'name':'top_motor','center':[front+length/2,cy,cz],'size':[length,side,side]})
    for plate in meta['plates']:
        if abs(plate['center'][0]-9.5)<.01:
            hole=[plate['center'][0],cy,cz]
            radii=plate.setdefault('hole_radii',[plate['hole_radius']]*len(plate['holes']))
            found=next((i for i,h in enumerate(plate['holes']) if np.linalg.norm(np.array(h)-hole)<1e-6),None)
            if found is None:plate['holes'].append(hole);radii.append(cfg['support_bearing_diameter_mm']/2)
            else:radii[found]=cfg['support_bearing_diameter_mm']/2
    for fr in frames:
        fr['parts']=[p for p in fr['parts'] if p['name'] not in REMOVED]
        fr['parts'].append({'name':'top_motor_shaft','p':[x,cy,cz],'q':[front,cy,cz],'radius':cfg['shaft_diameter_mm']/2})
        fr['gears']=[g for g in fr['gears'] if g['name']!='top_motor_pinion']
        right=next(g for g in fr['gears'] if g['name']=='R/distribution')
        # Equal-module external gears: tooth phase and angular velocity mesh with the right gear.
        phase=beta+np.pi-np.pi/new_teeth+(old_teeth/new_teeth)*(beta-right['phase'])
        fr['gears'].append({'name':'top_motor_pinion','center':[x,cy,cz],'phase':float(phase),
                            'mirror':1,'profile':'top_motor','face_width_mm':cfg['gear_face_width_mm']})
    meta['files_folder']='top_motor/same/' if meta.get('integrated_crank') else 'top_motor/split/'
    meta['top_motor_drive']={'pinion_teeth':new_teeth,'wing_gear_teeth':old_teeth,
                             'input_ratio':old_teeth/new_teeth,'center_mm':[x,cy,cz],
                             'description':'New top motor and 18T gear are a packaging concept, not part of the previous validation.'}
    dims.pop('Estimated running torque target',None)
    dims['Gear count']='3 (18T motor gear + two 34T wing gears)'
    dims['Motor gear reduction']='34:18 ≈ 1.89:1'
    return frames,meta,dims
