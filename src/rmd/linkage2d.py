"""Teaching diagram from the solved 3D frames; no separate motion model."""
import json
from pathlib import Path


def write_linkage_viewer(frames, path):
    import numpy as np
    from .direct_drive import settings
    from .direct_targets import curves
    from .config import CONFIG_DIR
    display=json.loads((CONFIG_DIR/'presentation/display.json').read_text())
    targets=curves(np.radians([f['theta_deg'] for f in frames]),settings())
    poses=[]
    for i,f in enumerate(frames):
        parts={p['name'].split('/',1)[1]:p for p in f['parts'] if p['name'].startswith('R/')}
        s=parts['rocker1']['p']
        def point(name,end):
            p=parts[name][end]
            return [p[1]-s[1], -(p[2]-s[2])]
        poses.append(dict(target_alpha=float(np.degrees(targets[0][i])),target_fold=float(np.degrees(targets[1][i])),theta=f['theta_deg'],alpha=f['alpha_deg'],fold=f['F_deg'],
            mu=[f['mu1_deg'],f['mu2_deg']],points={
            'O':point('crank1','p'),'A':point('crank1','q'),
            'B':point('rocker1','q'),'S':[0,0],
            'D':point('crank2_direct','q'),'E':point('inner_spar','q'),
            'Q':point('elbow_horn','q'),'T':point('outer_spar','q')}))
    template=(Path(__file__).parent/'templates/linkage2d.html').read_text()
    path.write_text(template.replace('__POSES__',json.dumps(poses,allow_nan=False)).replace('__CYCLE__',str(display['cycle_seconds'])))
    print('Wrote',path)
