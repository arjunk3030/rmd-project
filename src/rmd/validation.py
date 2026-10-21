"""Independent sampled kinematic screening; no saved pass flags are trusted."""
import numpy as np
from . import model, targets
from .config import SCREENS, SOLVER
from .fourbar import grashof_crank_rocker


def screen(design, branch1, branch2, n=None):
    n = n or SCREENS['screen_samples']
    th, at, ft = targets.sample_targets(n)
    sim = model.simulate(design, th, branch1, branch2)
    rep = {'assembles_full_cycle': bool(sim['ok']), 'screen_samples': n,
           'grid_step_deg': 360/n, 'passes': False}
    if not sim['ok']:
        rep['failed_checks'] = ['assembles_full_cycle']
        return rep
    alpha, fold = sim['alpha'], sim['F']
    derivative = (np.roll(alpha,-1)-np.roll(alpha,1))/(4*np.pi/n)
    down = derivative < -1e-8
    up = derivative > 1e-8
    nominal_down = th <= np.pi
    seam = model.simulate(design, np.array([0., 2*np.pi]), branch1, branch2)
    closure = max(np.linalg.norm(seam[k][1]-seam[k][0]) for k in ('A1','B1','E','P2','Q2','TIP'))
    def length_error(p,q,length):
        return float(np.max(np.abs(np.linalg.norm(p-q,axis=1)-length)))
    residual = max(length_error(sim['A1'], model.O, design['a1']),
                   length_error(sim['B1'], sim['A1'], design['b1']),
                   length_error(sim['B1'], model.S, design['c1']),
                   length_error(sim['P2'], model.S, design['a2']),
                   length_error(sim['Q2'], sim['P2'], design['b2']),
                   length_error(sim['Q2'], sim['E'], design['c2']))
    deg = np.degrees
    core=(np.degrees(th)>=SCREENS['core_downstroke_phase_deg'][0])&(np.degrees(th)<=SCREENS['core_downstroke_phase_deg'][1])&down
    rep.update({
        'grashof_1': grashof_crank_rocker(design['a1'],design['b1'],design['c1'],model.D1),
        'grashof_2': grashof_crank_rocker(design['a2'],design['b2'],design['c2'],model.L_IN),
        'mu1_min_deg': float(sim['mu1'].min()), 'mu2_min_deg': float(sim['mu2'].min()),
        'mu_screen_deg': SCREENS['mu_min_deg'],
        'u2_monotonic': bool(np.all(np.diff(sim['u2'])>0) or np.all(np.diff(sim['u2'])<0)),
        'u2_min_step_deg': float(deg(np.abs(np.diff(sim['u2'])).min())),
        'rms_alpha_deg': float(deg(np.sqrt(np.mean((alpha-at)**2)))),
        'max_alpha_err_deg': float(deg(np.abs(alpha-at).max())),
        'rms_F_upstroke_deg': float(deg(np.sqrt(np.mean((fold[~nominal_down]-ft[~nominal_down])**2)))),
        'max_F_downstroke_deg': float(deg(fold[down].max())) if down.any() else 1e9,
        'max_F_nominal_downstroke_deg': float(deg(fold[nominal_down].max())),
        'max_F_core_downstroke_deg':float(deg(fold[core].max())) if core.any() else 1e9,
        'min_F_deg': float(deg(fold.min())), 'max_F_deg': float(deg(fold.max())),
        'theta_at_max_F_deg': float(deg(th[fold.argmax()])),
        'shoulder_top_theta_deg': float(deg(th[alpha.argmax()])),
        'shoulder_bottom_theta_deg': float(deg(th[alpha.argmin()])),
        'downstroke_fold_tol_deg': SCREENS['downstroke_fold_tol_deg'],
        'cycle_closure_error_mm': float(closure), 'max_link_length_error_mm': residual,
        'branches_fixed_by_construction': True,
    })
    checks = {
        'packaging_bounds': all(lo-1e-8 <= design[k] <= hi+1e-8 for k,lo,hi in zip(SOLVER['parameter_keys'],SOLVER['lower_bounds'],SOLVER['upper_bounds'])),
        'grashof_1': rep['grashof_1'], 'grashof_2': rep['grashof_2'],
        'transmission_1': rep['mu1_min_deg'] >= SCREENS['mu_min_deg'],
        'transmission_2': rep['mu2_min_deg'] >= SCREENS['mu_min_deg'],
        'actual_downstroke_fold': rep['max_F_downstroke_deg'] <= SCREENS['downstroke_fold_tol_deg'],
        'core_downstroke_straightness':rep['max_F_core_downstroke_deg']<=SCREENS['core_downstroke_fold_max_deg'],
        'hyperextension': rep['min_F_deg'] >= -SCREENS['hyperextension_tol_deg'],
        'shoulder_tracking': rep['rms_alpha_deg'] <= SCREENS['shoulder_rms_max_deg'],
        'fold_tracking': rep['rms_F_upstroke_deg'] <= SCREENS['upstroke_fold_rms_max_deg'],
        'fold_peak_range': SCREENS['fold_peak_min_deg'] <= rep['max_F_deg'] <= SCREENS['fold_peak_max_deg'],
        'peak_fold_on_actual_upstroke': bool(up[fold.argmax()]),
        'periodic_closure': closure < 1e-7,
        'rigid_link_lengths': residual < 1e-7,
    }
    checks = {k: bool(v) for k,v in checks.items()}
    rep.update(checks=checks, failed_checks=[k for k,v in checks.items() if not v], passes=bool(all(checks.values())))
    return rep
