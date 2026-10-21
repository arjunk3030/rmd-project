"""Create viewer/movie frames from each supported design's checked geometry."""
import numpy as np
from .config import FIXED,BUILD
from .assembly import gear_outline
from .panels import panel_geometry


def make_frames(sim,geom,cfg,gear_function,placement,*,name,design_id,description):
    """placement converts canonical panel/rib points into the actual assembly."""
    variants={style:panel_geometry(sim,style=style,pitch_deg=0,direction=cfg.get('panel_direction',1)) for style in ('tapered','rectangular')}
    frames=[]
    for i,theta in enumerate(sim['thetas']):
        alpha=sim['alpha'];stroke='downstroke' if alpha[(i+1)%len(alpha)]<alpha[(i-1)%len(alpha)] else 'upstroke'
        frames.append({'theta_deg':float(np.degrees(theta)),'alpha_deg':float(np.degrees(alpha[i])),
            'F_deg':float(np.degrees(sim['F'][i])),'mu1_deg':float(sim['mu1'][i]),'mu2_deg':float(sim['mu2'][i]),'stroke':stroke,
            'parts':[{'name':n,'p':p['p'][i].tolist(),'q':p['q'][i].tolist(),'radius':p['radius']} for n,p in geom['parts'].items()],
            'panels':{n:[p[i].tolist() for p in q] for n,q in geom['panels'].items() if not n.startswith('body_cover/')},
            'panel_variants':{style:{n:[placement(p[i],n[0]).tolist() for p in quad] for n,quad in item[0].items()} for style,item in variants.items()},
            'rib_variants':{style:{n:{k:placement(rib[k][i],n[0]).tolist() for k in ('p','q')} for n,rib in item[1].items()} for style,item in variants.items()},
            'gears':gear_function(theta,cfg)})
    meta={'design_id':design_id,'name':name,'description':description,'cycle_seconds':BUILD['animation_cycle_seconds'],
          'scene_radius':(cfg['shoulder_spacing_mm']/2+FIXED['inner_length_mm']+FIXED['outer_length_mm'])*1.1,
          'inner_view_center_y':cfg['shoulder_spacing_mm']/2+cfg.get('wing_lengths_mm',{}).get('inner',FIXED['inner_length_mm'])/2,
          'boxes':geom['boxes'],'plates':geom['plates'],
          'covers':[[p[0].tolist() for p in q] for n,q in geom['panels'].items() if n.startswith('body_cover/')],
          'gear_profiles':{'local':gear_outline(0).tolist(),'distribution':gear_outline(0,gear=cfg['gear']).tolist()},
          'panel_pitch_deg':FIXED['panel_pitch_deg'],'panel_style':FIXED['panel_style'],
          'other_viewer':'direct_3d.html' if design_id=='compact' else 'compact_3d.html',
          'files_folder':'compact/' if design_id=='compact' else 'direct/'}
    points=np.array([p for fr in frames for part in fr['parts'] for p in (part['p'],part['q'])]+[p for fr in frames for quad in fr['panels'].values() for p in quad])
    static=np.array([np.array(b['center'])+np.array(b['size'])*np.array(sign)/2 for b in geom['boxes']+geom['plates'] for sign in [(-1,-1,-1),(1,1,1)]])
    points=np.vstack((points,static));meta['bounds_min']=(points.min(axis=0)-15).tolist();meta['bounds_max']=(points.max(axis=0)+15).tolist()
    return frames,meta
