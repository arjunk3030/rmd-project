"""Per-design energy, actuator and conditional prototype-strength estimates."""
import numpy as np
from .config import BUILD


def estimate(sim,geom,kind,cfg):
    n=len(sim['thetas']);step=2*np.pi/n;omega=2*np.pi/BUILD['animation_cycle_seconds']
    derivative=lambda x:(np.roll(x,-1,axis=0)-np.roll(x,1,axis=0))/(2*step)
    V=np.zeros(n);Ieff=np.zeros(n);rows=[];density=cfg.get('materials',{}).get('link_density_g_per_mm3',BUILD['mass_estimates_g']['link_density_g_per_mm3'])
    def member(name,p,q,mass_g):
        nonlocal V,Ieff
        center=(p+q)/2;length=float(np.linalg.norm(q[0]-p[0]));mass=mass_g/1000
        dc=derivative(center)/1000;d=q-p;angle=np.arctan2(d[:,2],d[:,1]);da=np.arctan2(np.sin(np.roll(angle,-1)-np.roll(angle,1)),np.cos(np.roll(angle,-1)-np.roll(angle,1)))/(2*step)
        V+=mass*9.80665*center[:,2]/1000;Ieff+=mass*np.sum(dc*dc,axis=1)+mass*(length/1000)**2/12*da*da
        rows.append({'part':name,'estimated_mass_g':mass_g})
    for name,p in geom['parts'].items():
        label=name.split('/')[-1]
        if label in ('crank1','coupler1','rocker1','crank2','rod2','rod2_direct','elbow_horn'):
            length=np.linalg.norm(p['q'][0]-p['p'][0]);member(name,p['p'],p['q'],density*(BUILD['link_width_mm']*length+np.pi*4**2)*BUILD['link_thickness_mm'])
        elif label in ('inner_spar','outer_spar'):
            key='inner_wing_with_hub' if label=='inner_spar' else 'outer_wing_with_hub'
            member(name,p['p'],p['q'],BUILD['mass_estimates_g'][key])
    torque=derivative(V)+.5*omega**2*derivative(Ieff);peak=float(abs(torque).max())
    # Rotating gears add constant inertia at steady speed, and additional startup torque.
    gear_count=6 if kind=='compact' else 2
    gearI=gear_count*(BUILD['mass_estimates_g']['gear_each']/1000)*(.025**2)/2
    startup=(float(Ieff.max())+gearI)*omega/2 # assumed 2 second speed ramp
    friction=2*BUILD['friction_allowance_Nm'];eff=BUILD['assumed_mesh_efficiency']**(2 if kind=='compact' else 1)
    factor=BUILD['torque_service_factor'];required=factor*(peak+startup+friction)/eff
    beta=sim['alpha']-sim['F'];db=np.arctan2(np.sin(np.roll(beta,-1)-np.roll(beta,1)),np.cos(np.roll(beta,-1)-np.roll(beta,1)))/(2*step)
    dd=derivative(db)*omega**2;E=sim['E']/1000;acc=derivative(derivative(E))*omega**2
    from . import model
    mass=BUILD['mass_estimates_g']['outer_wing_with_hub']/1000;L=sim.get('outer_length_mm',model.L_OUT)/1000
    r=np.column_stack((np.cos(beta),np.sin(beta)))*L/2
    elbow=mass*L*L/3*dd+mass*(r[:,0]*acc[:,1]-r[:,1]*acc[:,0])+mass*9.80665*r[:,0]
    horn=np.linalg.norm(sim['Q2']-sim['E'],axis=1)/1000
    force=float((abs(elbow)/np.maximum(horn*np.sin(np.radians(sim['mu2'])),1e-9)).max())
    design_force=force*factor
    overhang=3 if cfg.get('body_package')=='small_plywood_remote_drive' else abs(cfg['rear_crank_plane_x_mm']-cfg['elbow_bearing_centers_x_mm'][-1]) if kind=='direct' else 18
    d=cfg.get('shaft_diameter_mm',BUILD['shaft_diameter_mm']);I=np.pi*d**4/64;E_pa=BUILD['estimated_steel_E_GPa']*1000
    stress=32*design_force*overhang/(np.pi*d**3);deflection=design_force*overhang**3/(3*E_pa*I)
    rodname='R/rod2_direct' if kind=='direct' else 'R/rod2';rod=geom['parts'][rodname];rodL=float(np.linalg.norm(rod['q'][0]-rod['p'][0]))
    width,thickness=BUILD['link_width_mm'],BUILD['link_thickness_mm'];Irod=width*thickness**3/12
    rod_E=cfg.get('materials',{}).get('rod_E_GPa_assumed',1)
    buckling=np.pi**2*(rod_E*1000)*Irod/rodL**2 # assumed effective stiffness; measure actual stock
    return {'motor_count':1,'input_rpm':60/BUILD['animation_cycle_seconds'],'cycle_seconds':BUILD['animation_cycle_seconds'],
            'estimated_peak_constant_speed_torque_Nm':peak,'friction_allowance_Nm':friction,'startup_ramp_seconds_assumed':2,
            'startup_torque_allowance_Nm':startup,'assumed_path_efficiency':eff,'service_factor':factor,
            'required_running_torque_target_Nm':required,'peak_mechanical_power_W':peak*omega,
            'elbow_rod_force_peak_N':force,'factored_elbow_rod_force_N':design_force,
            'elbow_axle_overhang_mm':overhang,'estimated_elbow_shaft_bending_MPa':stress,
            'estimated_elbow_shaft_deflection_mm':deflection,
            'assumed_steel_yield_MPa':BUILD['estimated_steel_yield_MPa'],'assumed_steel_E_GPa':BUILD['estimated_steel_E_GPa'],
            'rod_material':cfg.get('materials',{}).get('link_stock','Original trial stock'), 'rod_E_GPa_assumed':rod_E,'ideal_pinned_rod_buckling_N':buckling,
            'conditional_strength_checks':{'elbow_shaft_bending':bool(stress<=BUILD['estimated_steel_yield_MPa']/BUILD['stress_safety_factor']),
                'elbow_shaft_deflection':bool(deflection<=BUILD['max_shaft_deflection_mm']),'ideal_rod_buckling':bool(design_force<buckling)},
            'mass_assumptions':rows,'running_torque_verified':False,'build_ready':False,
            'method':'tau=V_prime + 0.5*omega^2*Ieff_prime. Both wings and moving links; distributed rigid members, gravity and inertia.',
            'limits':'All masses, friction, link stiffness and steel properties are assumptions. Wood grain, ply quality, hole tear-out and fabric tension are unverified. Elbow cantilever estimate is not a full shaft/bearing/pin/gear-tooth strength analysis. No aerodynamics, impacts, compliance or resonance. Holding torque is not running torque; test the actual motor and hardware.'}
