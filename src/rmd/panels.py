"""Pitched, tapered covers and rigid finger-like ribs; all dimensions are inputs."""
import numpy as np
from .config import FIXED, BUILD
from . import model


def panel_geometry(sim, style=None, pitch_deg=None, direction=None):
    style=style or FIXED['panel_style'];pitch_deg=FIXED['panel_pitch_deg'] if pitch_deg is None else pitch_deg
    if style not in ('tapered','rectangular'):raise ValueError('Unknown panel style')
    direction=FIXED['membrane_direction'] if direction is None else direction
    if direction not in (-1,1):raise ValueError('Panel direction must be +1 or -1')
    beta=np.radians(pitch_deg);n=len(sim['thetas']);panels={};ribs={}
    def p3(uv,x,m):
        uv=np.broadcast_to(uv,(n,2))
        return np.column_stack([np.full(n,x),m*uv[:,0],uv[:,1]])
    for side,m in [('R',1),('L',-1)]:
        for name,uv,angle,length,relief,chord0,chord1,sweep,joint in [
            ('inner',model.S,sim['alpha'],sim.get('inner_length_mm',model.L_IN),sim.get('panel_root_relief_mm',FIXED['membrane_root_relief_mm']),FIXED['inner_panel_root_chord_mm'],FIXED['chord_inner_mm'],0,'S'),
            ('outer',sim['E'],sim['alpha']-sim['F'],sim.get('outer_length_mm',model.L_OUT),sim.get('panel_hinge_relief_mm',FIXED['membrane_hinge_relief_mm']),FIXED['chord_outer_mm'],FIXED['outer_panel_tip_chord_mm'],FIXED['outer_panel_sweep_mm'],'E')]:
            if style=='rectangular':chord0=chord1=FIXED[f'chord_{name}_mm'];sweep=0
            origin=p3(uv,0,m)
            span=np.column_stack([np.zeros(n),m*np.cos(angle),np.sin(angle)])
            chord=np.column_stack([np.full(n,np.cos(beta)),m*np.sin(angle)*np.sin(beta),-np.cos(angle)*np.sin(beta)])*direction
            a=origin+relief*span;b=origin+(length-sim.get('panel_hinge_relief_mm',FIXED['membrane_hinge_relief_mm']))*span
            a[:,0]=FIXED['membrane_front_x_mm'];b[:,0]=FIXED['membrane_front_x_mm']+sweep
            q0=a+chord0*chord;q1=b+chord1*chord
            panels[f'{side}/{name}_panel']=[a,b,q1,q0]
            root=p3(uv,0 if name=='inner' else BUILD['outer_spar_x_mm'],m)
            if name=='inner' and 'panel_root_relief_mm' in sim:root=root+20*span
            for j,fraction in enumerate((.3,.75) if name=='inner' else (.15,.55,.9)):
                end=q0+(q1-q0)*fraction
                ribs[f'{side}/{name}_finger_{j}']={'p':root,'q':end,'radius':1.,'joints':{f'{side}/{joint}'},'shape':'capsule3d'}
    return panels,ribs
