"""User-requested stylized motion; these are editable targets, not bat measurements."""
import numpy as np
from . import targets


def curves(theta,cfg):
    spec=cfg['motion_targets'];a=np.array([targets.alpha_target(t) for t in theta]);f=np.array([targets.F_target(t) for t in theta])
    lo,hi=spec['shoulder_min_deg'],spec['shoulder_max_deg']
    alpha=np.radians((lo+hi)/2)+(hi-lo)/50*a
    fold=np.radians(spec['fold_min_deg'])+(spec['fold_max_deg']-spec['fold_min_deg'])/50*f
    return alpha,fold
