"""Small-body direct six-bar synthesis; physical package lives in direct_package.py.

One remote actuator drives short supported shafts; each shaft carries shoulder
and elbow crank arms. Targets and ground geometry are design-specific.
"""
import json
import numpy as np
from scipy.optimize import least_squares,minimize
from .config import CONFIG_DIR,OUTPUT_DIR,BUILD
from .design_io import load_design
from . import model,compact_drive as compact
from .kinematics import dirs,intersection,sine_angle,effective_angle
from .assembly import assembly_geometry


def settings():
    return json.loads((CONFIG_DIR/'direct_drive.json').read_text())


class Problem:
    def __init__(self,n):
        self.cfg=settings();self.reference,self.rb1,self.rb2,_=load_design()
        _,self.O,self.rho=compact.layout(self.cfg)
        self.theta=np.linspace(0,2*np.pi,n,endpoint=False)
        self.target=model.simulate(self.reference,self.theta,self.rb1,self.rb2)
        from .direct_targets import curves
        self.target['alpha'],self.target['F']=curves(self.theta,self.cfg)

    def state(self,v,branchA=1,branchE=-1,desired=False):
        a,b,c,k,pa,ad,pd,h,eta,L=v;t=self.theta
        A=self.O+a*dirs(t+pa);B,h2a=intersection(model.S,c,A,b,branchA)
        at=self.target['alpha'];ft=self.target['F']
        alpha=at+(np.arctan2(B[:,1],B[:,0])-k-at+np.pi)%(2*np.pi)-np.pi
        E=self.cfg['wing_lengths_mm']['inner']*dirs(alpha);D=self.O+ad*dirs(t+pd)
        if desired:Q=E+h*dirs(alpha-ft+eta);h2e=np.ones(len(t));fold=ft
        else:
            Q,h2e=intersection(E,h,D,L,branchE)
            raw=alpha+eta-np.arctan2((Q-E)[:,1],(Q-E)[:,0])
            fold=ft+(raw-ft+np.pi)%(2*np.pi)-np.pi
        sim={'thetas':t,'ok':bool(min(h2a.min(),h2e.min())>0),'ok1':bool(h2a.min()>0),
             'A1':A,'B1':B,'alpha':alpha,'E':E,'P2':D,'Q2':Q,'F':fold,
             'TIP':E+self.cfg['wing_lengths_mm']['outer']*dirs(alpha-fold),
             'inner_length_mm':self.cfg['wing_lengths_mm']['inner'],'outer_length_mm':self.cfg['wing_lengths_mm']['outer'],
             'panel_root_relief_mm':self.cfg['panel_root_relief_mm'],'panel_hinge_relief_mm':self.cfg['panel_hinge_relief_mm'],
             'mu1':effective_angle(A-B,-B),'mu2':effective_angle(Q-D,Q-E)}
        return {'simulation':sim,'h2a':h2a,'h2e':h2e}

    def residual(self,v,branchA):
        a,b,c,k,pa,ad,pd,h,eta,L=v;s=self.state(v,branchA,desired=True);sim=s['simulation']
        mu=np.sin(np.radians(self.cfg['transmission_fit_deg']))
        return np.r_[35*(sim['alpha']-self.target['alpha']),np.linalg.norm(sim['Q2']-sim['P2'],axis=1)-L,
                     30*np.maximum(mu-np.sin(np.radians(sim['mu1'])),0),
                     30*np.maximum(mu-np.sin(np.radians(sim['mu2'])),0),
                     3*np.sqrt(np.maximum(-s['h2a'],0)),
                     10*max(2*(a+max(a,b,c,self.cfg.get('ground_mm',model.D1)))-(a+b+c+self.cfg.get('ground_mm',model.D1))+.1,0),
                     10*np.maximum(a-np.array([b,c,self.cfg.get('ground_mm',model.D1)]),0)]

    def constraints(self,v,ba,be):
        a,b,c,k,pa,ad,pd,h,eta,L=v;s=self.state(v,ba,be);sim=s['simulation'];f=sim['F'];t=self.theta;cfg=self.cfg
        down=np.roll(sim['alpha'],-1)<np.roll(sim['alpha'],1)
        core=(t>=np.pi/4)&(t<=3*np.pi/4)
        return np.r_[f-np.radians(cfg['minimum_fold_polish_deg']),np.radians(cfg.get('peak_fold_polish_max_deg',58))-f,
            sim['mu1']/90-cfg['transmission_polish_deg']/90,sim['mu2']/90-cfg['transmission_polish_deg']/90,
            s['h2a']/100-.01,s['h2e']/100-.01,
            (np.array([b,c,self.cfg.get('ground_mm',model.D1)])-a)/10,
            ((a+b+c+self.cfg.get('ground_mm',model.D1))-2*(a+max(a,b,c,self.cfg.get('ground_mm',model.D1)))-.1)/10,
            np.radians(cfg['downstroke_fold_polish_max_deg'])-np.where(down,f,-100),
            np.radians(cfg['downstroke_fold_polish_max_deg'])-f[t<=np.pi],
            np.radians(cfg['core_fold_polish_max_deg'])-f[core],np.max(f)-np.radians(cfg.get('peak_fold_polish_min_deg',45.5)),
            np.radians(self.cfg['motion_acceptance']['shoulder_min_range_deg'][1]-.5)-sim['alpha'].min(),sim['alpha'].max()-np.radians(30),
            np.radians(cfg['motion_acceptance']['shoulder_rms_max_deg'])**2-np.mean((sim['alpha']-self.target['alpha'])**2),
            np.radians(cfg['motion_acceptance']['fold_upstroke_rms_max_deg'])**2-np.mean((f[t>np.pi]-self.target['F'][t>np.pi])**2)]


def fit():
    cfg=settings();p=Problem(cfg['fit_samples']);lo=np.array(cfg['lower_bounds']);hi=np.array(cfg['upper_bounds'])
    seed=json.loads((CONFIG_DIR/'direct_seed.json').read_text())
    candidates=[(np.array(seed['parameters']),seed['branchA'],seed['branchE'])]
    rng=np.random.default_rng(cfg['random_seed']);best=None
    warm=least_squares(p.residual,np.clip(candidates[0][0],lo+1e-5,hi-1e-5),args=(candidates[0][1],),bounds=(lo,hi),max_nfev=500)
    best=(float(np.mean(warm.fun**2)),warm.x,candidates[0][1])
    candidates.append((warm.x,candidates[0][1],candidates[0][2]))
    for i in range(cfg['random_starts']):
        ba=1 if i%2 else -1
        if best and i%3:x=best[1]+rng.normal(size=10)*[2,4,4,.3,.4,3,.4,4,.4,8];ba=best[2]
        else:x=lo+(hi-lo)*rng.uniform(.1,.9,10)
        r=least_squares(p.residual,np.clip(x,lo+1e-5,hi-1e-5),args=(ba,),bounds=(lo,hi),max_nfev=600)
        score=float(np.mean(r.fun**2))
        if best is None or score<best[0]:best=(score,r.x,ba)
    for be in (-1,1):candidates.append((best[1],best[2],be))
    p=Problem(cfg['polish_samples']);solutions=[];attempts=[]
    for x,ba,be in candidates:
        def cost(v):
            sim=p.state(v,ba,be)['simulation']
            return float(np.mean((sim['alpha']-p.target['alpha'])**2)+cfg['reference_fold_weight']*np.mean((sim['F']-p.target['F'])**2))
        if p.constraints(x,ba,be).min()>-1e-7:solutions.append((cost(x),x,ba,be))
        r=minimize(cost,np.clip(x,lo,hi),method='SLSQP',bounds=list(zip(lo,hi)),
            constraints=[{'type':'ineq','fun':lambda v:p.constraints(v,ba,be)}],
            options={'maxiter':500,'ftol':1e-12})
        sim=p.state(r.x,ba,be)['simulation'];attempts.append({'parameters':r.x.tolist(),'branchA':ba,'branchE':be,'violation':float(p.constraints(r.x,ba,be).min()),'message':str(r.message),'shoulder':[float(np.degrees(sim['alpha'].min())),float(np.degrees(sim['alpha'].max()))],'fold':[float(np.degrees(sim['F'].min())),float(np.degrees(sim['F'].max()))],'mu':[float(sim['mu1'].min()),float(sim['mu2'].min())]})
        if p.constraints(r.x,ba,be).min()>-1e-7:solutions.append((float(r.fun),r.x,ba,be))
    (OUTPUT_DIR/'direct/synthesis_attempts.json').write_text(json.dumps(attempts,indent=2)+'\n')
    if not solutions:raise ValueError('Direct-drive synthesis did not produce an accepted full-cycle solution')
    _,v,ba,be=min(solutions,key=lambda r:r[0]);return v,ba,be


def gears(theta,cfg):
    # Both geared shafts turn 1:1 in opposite world directions; crank arms
    # have independent fixed mounting offsets recorded in the zero pose.
    _,o,rho=compact.layout(cfg);half=cfg['shoulder_spacing_mm']/2;z=cfg['gear']['teeth'];x=cfg['gear_plane_x_mm']
    return [{'name':'R/distribution','center':[x,half+o[0],o[1]],'phase':float(theta+rho),'mirror':1,'profile':'distribution','face_width_mm':cfg['gear']['face_width_mm'],'interfaces':['R/pin_D','R/fastener_D']},
            {'name':'L/distribution','center':[x,-half-o[0],o[1]],'phase':float(theta+rho-np.pi/z),'mirror':-1,'profile':'distribution','face_width_mm':cfg['gear']['face_width_mm'],'interfaces':['L/pin_D','L/fastener_D']}]


def geometry(v,ba,be,theta):
    from .direct_package import geometry as package
    p=Problem(len(theta));p.theta=np.asarray(theta);p.target=model.simulate(p.reference,p.theta,p.rb1,p.rb2)
    from .direct_targets import curves
    p.target['alpha'],p.target['F']=curves(p.theta,p.cfg)
    return package(p.state(v,ba,be)['simulation'],p.cfg)
