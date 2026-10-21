"""Read-only evidence: dense motion checks, source map and local loss landscape."""
import csv
import inspect
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .config import ROOT,OUTPUT_DIR,BUILD
from .direct_drive import Problem,settings
from .designs import get_direct
from .direct_targets import curves
from .kinematics import effective_angle


def generate():
    out=OUTPUT_DIR/'diagnostics';out.mkdir(exist_ok=True)
    v,ba,be,_=get_direct(allow_fit=False);cfg=settings();p=Problem(7200)
    sim=p.state(v,ba,be)['simulation'];theta=np.degrees(p.theta)
    actual=np.degrees(np.column_stack((sim['alpha'],sim['F'])))
    target=np.degrees(np.column_stack(curves(p.theta,cfg)))
    minima={key:{'degrees':float(sim[key].min()),'input_degrees':float(theta[sim[key].argmin()])} for key in ('mu1','mu2')}
    display=json.loads((ROOT/'config/presentation/display.json').read_text())
    numbers={'scope':'Same frozen design; 7200 poses at 0.05 degrees. No fitting.',
             'links_mm':dict(zip(['a','b','c','aD','h','L'],v[[0,1,2,5,7,9]].tolist())),
             'mounting_deg':dict(zip(['kappa','phase_A','phase_B','eta'],np.degrees(v[[3,4,6,8]]).tolist())),
             'transmission_minima':minima,'input_travel_deg':360,'modeled_rpm':60/BUILD['animation_cycle_seconds'],
             'playback_cycle_seconds':display['cycle_seconds'],'physical_stock_mm':BUILD['link_thickness_mm'],'intended_stock_mm':6.35}
    (out/'numbers.json').write_text(json.dumps(numbers,indent=2)+'\n')
    with (out/'motion_dense.csv').open('w') as f:
        w=csv.writer(f);w.writerow(['crank_deg','shoulder_actual_deg','shoulder_target_deg','fold_actual_deg','fold_target_deg','mu_shoulder_deg','mu_elbow_deg'])
        w.writerows(zip(theta,actual[:,0],target[:,0],actual[:,1],target[:,1],sim['mu1'],sim['mu2']))
    fig,axes=plt.subplots(3,1,figsize=(10,8),sharex=True,layout='constrained')
    for i,title in enumerate(('Shoulder angle','Elbow bend')):
        axes[i].plot(theta,target[:,i],'--',color='#7c8795',label='Target')
        axes[i].plot(theta,actual[:,i],color=('#168a96','#ce7634')[i],label='Frozen design')
        axes[i].set_ylabel(title+' (°)');axes[i].legend(loc='upper right');axes[i].grid(alpha=.2)
    axes[2].plot(theta,sim['mu1'],label='Shoulder',color='#438bff');axes[2].plot(theta,sim['mu2'],label='Elbow',color='#ff8c1a')
    axes[2].axhline(40,color='#bd3640',ls='--',label='40° requirement');axes[2].set(xlabel='Input crank angle (°)',ylabel='Transmission (°)',xlim=(0,360));axes[2].legend(ncol=3);axes[2].grid(alpha=.2)
    fig.savefig(out/'motion_and_transmission.png',dpi=150);plt.close(fig)
    # A slice through the existing objective, not a new optimization run.
    q=Problem(180);xs=np.linspace(v[0]-.6,v[0]+.6,41);ys=np.linspace(v[7]-2,v[7]+2,41)
    loss=np.full((len(ys),len(xs)),np.nan);feasible=np.zeros_like(loss,dtype=bool)
    for j,h in enumerate(ys):
        for i,a in enumerate(xs):
            x=v.copy();x[0]=a;x[7]=h;s=q.state(x,ba,be)['simulation']
            if s['ok']:
                loss[j,i]=np.mean((s['alpha']-q.target['alpha'])**2)+cfg['reference_fold_weight']*np.mean((s['F']-q.target['F'])**2)
                feasible[j,i]=q.constraints(x,ba,be).min()>=-1e-7 and np.all(x>=cfg['lower_bounds']) and np.all(x<=cfg['upper_bounds'])
    fig,ax=plt.subplots(figsize=(9,5),layout='constrained')
    im=ax.pcolormesh(xs,ys,loss,shading='auto',cmap='viridis');fig.colorbar(im,ax=ax,label='J (weighted mean squared angular error, rad²)')
    if feasible.any() and not feasible.all():ax.contour(xs,ys,feasible.astype(int),levels=[.5],colors='white',linewidths=1.4)
    ax.plot(v[0],v[7],'*',color='#ffcb5b',ms=15,label='Frozen design');ax.legend()
    ax.set(xlabel='Shoulder crank a (mm)',ylabel='Outer-wing output lever h (mm)',title='Local loss landscape — other eight parameters fixed')
    fig.savefig(out/'loss_landscape.png',dpi=150);plt.close(fig)
    sources=[('Actual loop equations',Problem.state),('Initial least-squares residuals',Problem.residual),('Hard refinement constraints',Problem.constraints),('Transmission-angle calculation',effective_angle)]
    rows='\n'.join(f'| {label} | `{str(inspect.getsourcefile(fn)).replace(str(ROOT)+"/", "")}:{inspect.getsourcelines(fn)[1]}` |' for label,fn in sources)
    params='\n'.join(f'| {name} | {value:.6f} mm |' for name,value in numbers['links_mm'].items())
    text=f'''# Where the numbers come from

These are recomputed from the frozen parameter vector, not copied PASS flags.

| Link parameter | Saved value |
| --- | ---: |
{params}

Canonical values and branches: `outputs/direct/dimensions.json`. Freeze guard: `config/presentation/frozen_design.json`.

| Reported quantity | Recomputed result |
| --- | --- |
| Shoulder minimum transmission | {minima['mu1']['degrees']:.6f}° at crank {minima['mu1']['input_degrees']:.2f}° |
| Elbow minimum transmission | {minima['mu2']['degrees']:.6f}° at crank {minima['mu2']['input_degrees']:.2f}° |
| Input travel | 360° per cycle |
| Nominal physical speed | 15 rpm from 60 / 4 seconds in config/build.json |
| Motion samples | 7200; 0.05° increments |

| Question | Source |
| --- | --- |
{rows}
| Desired angles | config/direct_drive.json → motion_targets; config/targets.json → samples; src/rmd/direct_targets.py |
| Final objective and solver | src/rmd/direct_drive.py → fit → cost; mean shoulder error² + 0.35 mean fold error² |
| Numerical package checks | outputs/direct/validation.json; outputs/single_face/validation.json |

## Reading the plots

Dashed motion curves are desired, solid curves are actual. The loss map varies only a and h, retaining the other eight parameters and both branches. Its white boundary, if present, outlines the sampled refinement constraints plus variable bounds. Blank regions fail closure. The gold star is the submitted geometry. This is a local sensitivity illustration, not proof of a global optimum or a new synthesized design. No physical collision audit is run for perturbed map points.

Lower loss alone is not a better machine: it can violate transmission, fold or size constraints. A thin feasible region may be missed by this coarse map. The same-face 3D variant remains a known collision experiment. No actuator has been selected, and 6.35 mm plywood has not been packaged.
'''
    (out/'numbers.md').write_text(text)
    (out/'index.html').write_text('''<!doctype html><html lang="en"><meta charset="utf-8"><title>Design evidence</title><style>body{font:16px/1.6 system-ui;max-width:1050px;margin:30px auto;padding:20px;background:#f3f5f8;color:#172436}img{max-width:100%;background:white}a{color:#245db1}</style><a href="../index.html">← Four demos</a><h1>Motion and transmission evidence</h1><p>Same frozen six-bar dimensions. Dashed curves are targets; solid curves are actual motion.</p><img src="motion_and_transmission.png" alt="Shoulder, elbow and transmission angles throughout one revolution"><h2>Local sensitivity of the motion loss</h2><p>Two variables changed virtually; other eight fixed. Gold star: frozen design. White boundary: sampled numerical feasibility, when visible. This is not re-optimization or a collision-checked design family.</p><img src="loss_landscape.png" alt="Loss landscape versus shoulder crank and output lever lengths"><p><a href="numbers.md">Numbers and code locations</a> · <a href="numbers.json">Numerical results JSON</a> · <a href="motion_dense.csv">Dense motion CSV</a></p></html>''')
    print('Wrote evidence plots and source map:',out)
