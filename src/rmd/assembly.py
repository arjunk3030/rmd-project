"""Single source of physical geometry for clearance, rendering and CAD exports.

x is fore-aft. All link pin axes are parallel to x. Couplers use separate
axial lap-joint planes, joined by M3 pins; planar pivot distances are unchanged.
"""
import numpy as np
from .config import FIXED, BUILD
from . import model


def gear_outline(phase, mirror=1, gear=None):
    """Standard unshifted involute spur profile; no root fillet (prototype only)."""
    gear=BUILD['gear'] if gear is None else gear;m=gear['module_mm'];z=gear['teeth'];rp=m*z/2
    rb=rp*np.cos(np.radians(gear['pressure_angle_deg']));root=rp-1.25*m;tip=rp+m
    inv=lambda r: np.sqrt(max((r/rb)**2-1,0))-np.arccos(min(rb/r,1))
    half=lambda r: np.pi/(2*z)-gear['tooth_thinning_mm']/(2*rp)+inv(rp)-inv(r)
    points=[]
    for k in range(z):
        angle=phase+2*np.pi*k/z
        for r in np.linspace(max(root,rb),tip,5):
            t=angle-half(r);points.append([mirror*r*np.cos(t),r*np.sin(t)])
        for t in np.linspace(angle-half(tip),angle+half(tip),4)[1:]:
            points.append([mirror*tip*np.cos(t),tip*np.sin(t)])
        for r in np.linspace(tip,max(root,rb),5)[1:]:
            t=angle+half(r);points.append([mirror*r*np.cos(t),r*np.sin(t)])
        for t in np.linspace(angle+half(root),angle+2*np.pi/z-half(root),4)[1:]:
            points.append([mirror*root*np.cos(t),root*np.sin(t)])
    return np.array(points)


def assembly_geometry(design, sim):
    n=len(sim['thetas']);sy=0.;layers=FIXED['layer_x_mm']
    def point(uv,x,m):
        uv=np.broadcast_to(uv,(n,2))
        return np.column_stack([np.full(n,x),m*(sy+uv[:,0]),uv[:,1]])
    parts={};panels={};nodes={};boxes=[];plates=[]
    radius=BUILD['link_thickness_mm']/2
    def segment(name,p,q,r,joints):
        parts[name]={'p':p,'q':q,'radius':r,'joints':set(joints)}
    for side,m in [('R',1),('L',-1)]:
        x1,x1r,x2,x2r=layers['linkage1'],layers['linkage1_rod'],layers['linkage2'],layers['linkage2_rod']
        pts={key:point(uv,x,m) for key,uv,x in [
            ('O',model.O,x1),('A',sim['A1'],x1),('B',sim['B1'],x1),('S1',model.S,x1),
            ('Ar',sim['A1'],x1r),('Br',sim['B1'],x1r),
            ('S2',model.S,x2),('P',sim['P2'],x2),('Q',sim['Q2'],x2),('E2',sim['E'],x2),
            ('Pr',sim['P2'],x2r),('Qr',sim['Q2'],x2r),
            ('S',model.S,0),('E',sim['E'],0),('Eouter',sim['E'],BUILD['outer_spar_x_mm']),('T',sim['TIP'],BUILD['outer_spar_x_mm'])]}
        nodes[side]=pts
        specs=[('crank1','O','A',('O','A')),('coupler1','Ar','Br',('A','B')),
               ('rocker1','S1','B',('S','B')),('crank2','S2','P',('S','P')),
               ('rod2','Pr','Qr',('P','Q')),('elbow_horn','E2','Q',('E','Q')),
               ('inner_spar','S','E',('S','E')),('outer_spar','Eouter','T',('E','T')),
               ('pin_A','A','Ar',('A',)),('pin_B','B','Br',('B',)),
               ('pin_P','P','Pr',('P',)),('pin_Q','Q','Qr',('Q',))]
        for name,p,q,joints in specs:
            # Flat links use a conservative capsule enclosing their 8 mm width.
            # Lap-plane separation is checked with axial thickness separately.
            segment(f'{side}/{name}',pts[p],pts[q],1.5 if 'pin_' in name else BUILD['link_width_mm']/2,
                    [f'{side}/{j}' for j in joints])
            parts[f'{side}/{name}']['axial_half_thickness']=radius
        for label,a,b in [('A','A','Ar'),('B','B','Br'),('P','P','Pr'),('Q','Q','Qr')]:
            p,q=pts[a].copy(),pts[b].copy()
            p[:,0]=np.minimum(pts[a][:,0],pts[b][:,0])-(BUILD['link_thickness_mm']/2+BUILD['fastener_head_height_mm'])
            q[:,0]=np.maximum(pts[a][:,0],pts[b][:,0])+(BUILD['link_thickness_mm']/2+BUILD['fastener_head_height_mm'])
            segment(f'{side}/fastener_{label}',p,q,BUILD['fastener_head_radius_mm'],[f'{side}/{label}'])
        for name,uv,key,joint in [('elbow_shaft',sim['E'],'elbow_shaft_x_mm','E')]:
            start,end=BUILD[key]
            segment(f'{side}/{name}',point(uv,start,m),point(uv,end,m),BUILD['shaft_diameter_mm']/2,[f'{side}/{joint}'])
        # Cylindrical bearing housings and shaft couplers; end faces are exact x intervals.
        root=BUILD['root_hub'];elbow=BUILD['elbow_hub']
        for name,uv,x0,x1,r,joint in [
            ('root_hub',model.S,root['x_min_mm'],root['x_max_mm'],root['radius_mm'],'S'),
            ('elbow_hub',sim['E'],elbow['x_min_mm'],elbow['x_max_mm'],elbow['radius_mm'],'E'),
            ('outer_wing_clamp',sim['E'],-8,-4,6,'E'),
]:
            segment(f'{side}/{name}',point(uv,x0,m),point(uv,x1,m),r,[f'{side}/{joint}'])
        clamps=BUILD['crank_clamp_hubs']
        for name,uv,span,joint in [('clamp_crank1',model.O,clamps['crank1_x_mm'],'O'),('clamp_crank2',model.S,clamps['crank2_x_mm'],'S'),('clamp_outer_horn',sim['E'],clamps['outer_horn_x_mm'],'E')]:
            segment(f'{side}/{name}',point(uv,span[0],m),point(uv,span[1],m),clamps['crank2_radius_mm'] if name=='clamp_crank2' else clamps['radius_mm'],[f'{side}/{joint}'])
    from .panels import panel_geometry
    panels,ribs=panel_geometry(sim)
    parts.update(ribs)
    geometry={'parts':parts,'panels':panels,'nodes':nodes,'boxes':boxes,'plates':plates}
    return geometry


def add_root_bosses(geometry,design_id):
    """Include the widened drilled roots used in the fabrication templates."""
    roots={'crank1':('O',6),'rocker1':('S',12 if design_id=='compact' else 6),
           'elbow_horn':('E',6),'crank2':('S',6)}
    for name,p in list(geometry['parts'].items()):
        label=name.split('/')[-1]
        if label not in roots:continue
        joint,radius=roots[label];side=name.split('/')[0]
        geometry['parts'][side+'/root_boss_'+label]={'p':p['p'].copy(),'q':p['p'].copy(),
            'radius':radius,'axial_half_thickness':BUILD['link_thickness_mm']/2,'joints':{side+'/'+joint}}
    return geometry
