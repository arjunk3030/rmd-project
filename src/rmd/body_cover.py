"""Editable stationary plywood silhouette, included in the moving-part audit."""
import numpy as np


def add_cover(geometry,cfg,n):
    cover=cfg.get('body_cover',{})
    if cover.get('enabled'):
        x=cover['plane_x_mm']
        for i,quad in enumerate(cover['quads_yz_mm']):
            geometry['panels'][f'body_cover/{i}']=[np.tile([x,y,z],(n,1)) for y,z in quad]
    return geometry
