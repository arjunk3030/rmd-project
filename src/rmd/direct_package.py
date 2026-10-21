"""Small plywood body with remote actuator: geometry shared by audit and rendering.

The shaft drive is a 1:1 20T/20T timing belt from the pedestal. A 24T pair
counter-rotates the two O shafts. Front/rear crank arms are separate from gears.
"""
import numpy as np
from .config import BUILD
from . import model,compact_drive as compact
from .panels import panel_geometry
from .body_cover import add_cover


def geometry(sim,cfg):
    n=len(sim['thetas']);half,O,rho=compact.layout(cfg);parts={};plates=[];boxes=[]
    def world(uv,x,m):
        uv=np.broadcast_to(uv,(n,2));return np.column_stack((np.full(n,x),m*(half+uv[:,0]),uv[:,1]))
    def part(name,p,q,r,j,flat=False,shape=None):
        parts[name]={'p':p,'q':q,'radius':r,'joints':set(j)}
        if flat:parts[name]['axial_half_thickness']=1.5
        if shape:parts[name]['shape']=shape
    def axle(name,uv,span,r,j,m):part(name,world(uv,span[0],m),world(uv,span[1],m),r,{j})
    panels,ribs=panel_geometry(sim,direction=cfg['panel_direction'])
    placed={}
    for side,m in [('R',1),('L',-1)]:
        j=lambda k:side+'/'+k;extra=0 if side=='R' else cfg['left_layer_spread_mm']
        xa=cfg['front_crank_plane_x_mm'];ra=cfg['front_rod_plane_x_mm']
        xd=cfg['rear_crank_plane_x_mm']+extra;rd=cfg['rear_rod_plane_x_mm']+extra
        xw=cfg['wing_plane_x_mm']+extra;xh=xw+4.5;xb=cfg['front_rocker_plane_x_mm']
        for name,a,b,x,js in [('crank1',O,sim['A1'],xa,['O','A']),('coupler1',sim['A1'],sim['B1'],ra,['A','B']),
             ('rocker1',model.S,sim['B1'],xb,['S','B']),('crank2_direct',O,sim['P2'],xd,['O','D']),
             ('rod2_direct',sim['P2'],sim['Q2'],rd,['D','Q']),('elbow_horn',sim['E'],sim['Q2'],xh,['E','Q'])]:
            part(j(name),world(a,x,m),world(b,x,m),4,{j(k) for k in js},True)
        for key,uv,x0,x1 in [('A',sim['A1'],xa,ra),('B',sim['B1'],xb,ra),('D',sim['P2'],xd,rd),('Q',sim['Q2'],xh,rd)]:
            axle(j('pin_'+key),uv,[min(x0,x1)-1.5,max(x0,x1)+1.5],1.5,j(key),m)
            axle(j('fastener_'+key),uv,[min(x0,x1)-3.5,min(x0,x1)-1.5],3,j(key),m)
            axle(j('nut_'+key),uv,[max(x0,x1)+1.5,max(x0,x1)+3.5],3,j(key),m)
        axle(j('motor_shaft'),O,[xa-2,xd+2],1.5,j('O'),m)
        axle(j('shoulder_shaft'),model.S,[xb-2,xw+2],1.5,j('S'),m)
        axle(j('elbow_shaft'),sim['E'],[xw-8,xh+2],1.5,j('E'),m)
        # 8 mm OD small shaft hubs; 9 mm OD short elbow bushing carrier.
        for name,uv,span,key,r in [('clamp_crank1',O,[xa+1.5,xa+4],'O',4),('clamp_crank2',O,[xd-4,xd-1.5],'O',4),
            ('clamp_rocker1',model.S,[xb+1.5,xb+4],'S',4),('root_clamp',model.S,[xw-1.5,xw+2],'S',4),
            ('elbow_hub',sim['E'],[xw-1.5,xw+1.5],'E',4.5),('outer_wing_clamp',sim['E'],[xw-8,xw-4],'E',4),
            ('gear_hub',O,[-2.5,.5],'O',4)]:axle(j(name),uv,span,r,j(key),m)
        part(j('inner_spar'),world(model.S,xw,m),world(sim['E'],xw,m),2,{j('S'),j('E')},True)
        part(j('outer_spar'),world(sim['E'],xw-6,m),world(sim['TIP'],xw-6,m),2,{j('E'),j('TIP')},True)
        for name,rib in ribs.items():
            if not name.startswith(side+'/'):continue
            p=compact.transform(rib['p'],side,cfg)+[xw,0,0];q=compact.transform(rib['q'],side,cfg)+[xw,0,0]
            parts[name]=dict(rib,p=p,q=q)
        for name,quad in panels.items():
            if name.startswith(side+'/'):placed[name]=[compact.transform(p,side,cfg)+[xw,0,0] for p in quad]
    for x in (-9.5,9.5):
        holes=[[x,m*half,0] for m in (-1,1)]+[[x,m*(half+O[0]),O[1]] for m in (-1,1)]
        plates.append({'name':f'common_bearing_plate_{x:g}','center':[x,0,-14],'size':[3,cfg['shoulder_spacing_mm']+12,44],
                       'holes':holes,'hole_radius':3.05})
    # Fixed posts are below the crank sweep and reach the common plates' lower edges.
    for x in (-9.5,9.5):
        boxes.append({'name':f'stand_leg_{x:g}','center':[x,-16,-94],'size':[3,6,116]})
    for y in (-17,0):
        for z in (5,):
            part(f'frame_spacer_{y}_{z}',np.tile([-8,y,z],(n,1)),np.tile([8,y,z],(n,1)),1.5,{'frame'})
    # Two 20T, 2 mm pitch pulleys: equal rotation, 100 mm centers -> 240 mm pitch belt.
    y=half+O[0];z=O[1];px=cfg['belt']['plane_x_mm'];R=cfg['belt']['teeth']*cfg['belt']['pitch_mm']/(2*np.pi);C=cfg['belt']['center_distance_mm']
    for name,zz,key in [('body_pulley',z,'R/O'),('pedestal_pulley',z-C,'drive/M')]:
        part(name,np.tile([px-3,y,zz],(n,1)),np.tile([px+3,y,zz],(n,1)),R+1,{key})
    for sign in (-1,1):
        part(f'belt_span_{sign}',np.tile([px,y+sign*R,z],(n,1)),np.tile([px,y+sign*R,z-C],(n,1)),1,{'R/O','drive/M'},shape='capsule3d')
    # Reservation for a measured single-output continuous actuator, outside bat body.
    boxes.append({'name':'drive/actuator_reservation','center':[34,y,z-C],'size':[40,20,40]})
    part('drive/output_shaft',np.tile([px,y,z-C],(n,1)),np.tile([14,y,z-C],(n,1)),1.5,{'drive/M'})
    boxes.append({'name':'base','center':cfg['base_center_mm'],'size':cfg['base_size_mm']})
    return add_cover({'parts':parts,'panels':placed,'boxes':boxes,'plates':plates,'simulation':sim},cfg,n)
