"""
LEGACY: synthesis of the older geared four-bar candidate.

Not the current direct six-bar optimizer; that is direct_drive.py → fit().
Still used by redesign_worker when changed shared inputs require rebuilding
the saved reference. Retained as an active compatibility dependency.

Historical synthesis stages:

  1. Freudenstein seed, linkage 1 (body frame). The rocker mounting
     offset kappa1 is unknown a priori, so the seed search grids over
     kappa1 and assembly branch and keeps the candidate that best fits
     the full target cycle and passes the screens.
  2. Freudenstein seed, linkage 2 (inner-wing frame), using linkage 1's
     ACTUAL simulated alpha (per Approach C) to form u2 at the design
     samples. Grids over drive phase delta, elbow offset eta, and branch.
  3. Joint least-squares optimisation of all nine OPTIMIZED numbers
     against the full target cycle, with the straight downstroke treated
     as an interval (fold tolerance), plus soft screen penalties.
  4. Screening report on a fine grid.

Use the isolated `python3 run_all.py redesign NAME` workflow.
This module writes the reference dimensions into that run’s output directory.
"""
import json
import os
import sys

import numpy as np
from scipy.optimize import least_squares, minimize


from .config import ESTIMATED_SAMPLES, FIXED, FREUDENSTEIN_SAMPLE_IDX, SCREENS, SOLVER, OUTPUT_DIR, input_snapshot, input_digest
from .fourbar import freudenstein, grashof_crank_rocker
from . import model
from . import targets
from .validation import screen

D2R = np.pi / 180.0
MU_MIN = SCREENS["mu_min_deg"]
F_TOL = SCREENS["downstroke_fold_tol_deg"] * D2R
HYPER_TOL = SCREENS["hyperextension_tol_deg"] * D2R


def _within_bounds(sol, linkage):
    bounds = dict(zip(SOLVER['parameter_keys'],zip(SOLVER['lower_bounds'],SOLVER['upper_bounds'])))
    # An analytical B seed may have a short crank; final optimization must
    # obey the larger hardware minimum, independently checked in validation.
    return all((3.0 if linkage==2 and key=='a' else bounds[f'{key}{linkage}'][0]) <= sol[key] <= bounds[f'{key}{linkage}'][1] for key in ('a','b','c'))


def _sample(idx):
    t, a_deg, f_deg = ESTIMATED_SAMPLES[idx]
    return 2 * np.pi * t, a_deg * D2R, f_deg * D2R


# --------------------------------------------------------------------------
# Stage 1: linkage 1 seed
# --------------------------------------------------------------------------
def seed_linkage1(n_sim=72):
    ths = np.linspace(0, 2 * np.pi, n_sim, endpoint=False)
    _, a_t, _ = targets.sample_targets(n_sim)
    best = None
    idx = FREUDENSTEIN_SAMPLE_IDX["linkage1"]
    samples = sorted([_sample(i) for i in idx], key=lambda row: row[0])
    for kappa in np.arange(-np.pi, np.pi, np.pi / 12):
        pairs = [((th + model.CRANK1_PHASE - model.GAMMA1),
                  (al + kappa - model.GAMMA1)) for th, al, _ in samples]
        sol = freudenstein(pairs, model.D1)
        if sol is None or not _within_bounds(sol, 1) or not grashof_crank_rocker(sol["a"], sol["b"], sol["c"], sol["d"]):
            continue
        for branch in (1, -1):
            d = {"a1": sol["a"], "b1": sol["b"], "c1": sol["c"], "kappa1": kappa,
                 "a2": 10.0, "b2": model.L_IN, "c2": 10.0, "eta": 0.0, "delta": 0.0}
            sim = model.simulate(d, ths, branch1=branch, branch2=1)
            if not sim["ok1"]:
                continue
            precision = model.simulate(d, np.array([row[0] for row in samples]), branch1=branch)
            errors = precision["alpha"]-np.array([row[1] for row in samples])
            if np.max(np.abs(np.arctan2(np.sin(errors),np.cos(errors)))) > 1e-6:
                continue
            rms = float(np.sqrt(np.mean((sim["alpha"] - a_t) ** 2)))
            mu_pen = max(0.0, MU_MIN - np.nanmin(sim["mu1"])) * D2R
            score = rms + 2.0 * mu_pen
            if best is None or score < best[0]:
                best = (score, d, branch, rms, float(np.nanmin(sim["mu1"])))
    if best is None:
        raise RuntimeError("linkage 1: no Freudenstein seed passed assembly/Grashof")
    _, d, branch, rms, mu = best
    return d, branch, {"rms_alpha_deg": rms / D2R, "mu1_min_deg": mu}


# --------------------------------------------------------------------------
# Stage 2: linkage 2 seed (uses linkage 1's actual alpha)
# --------------------------------------------------------------------------
def seed_linkage2(design1, branch1, n_sim=72):
    ths = np.linspace(0, 2 * np.pi, n_sim, endpoint=False)
    sim1 = model.simulate(design1, ths, branch1=branch1, branch2=1)
    if not sim1["ok1"]:
        raise RuntimeError("linkage 1 seed does not assemble over the full cycle")
    _, _, f_t = targets.sample_targets(n_sim)
    idx = FREUDENSTEIN_SAMPLE_IDX["linkage2"]
    samples = sorted([_sample(i) for i in idx], key=lambda row: row[0])
    sample_theta = np.array([row[0] for row in samples])
    sample_alpha = model.simulate(design1, sample_theta, branch1=branch1)["alpha"]
    alpha_of = lambda th: float(sample_alpha[np.flatnonzero(sample_theta == th)[0]])
    best = None
    for delta in np.arange(-np.pi, np.pi, np.pi / 36):
        for eta in np.arange(-np.pi, np.pi, np.pi / 36):
            pairs = [((model.DRIVE_SIGN * th + delta - alpha_of(th)), (eta - f))
                     for th, _, f in samples]
            sol = freudenstein(pairs, model.L_IN)
            if sol is None or not _within_bounds(sol, 2) or not grashof_crank_rocker(sol["a"], sol["b"], sol["c"], sol["d"]):
                continue
            for branch2 in (1, -1):
                d = dict(design1, a2=sol["a"], b2=sol["b"], c2=sol["c"],
                         eta=eta, delta=delta)
                sim = model.simulate(d, ths, branch1=branch1, branch2=branch2)
                if not sim["ok"]:
                    continue
                # fold error: pointwise on upstroke, interval on downstroke
                down = ths <= np.pi
                err = np.where(
                    down,
                    np.maximum(0.0, sim["F"] - F_TOL) + np.maximum(0.0, -sim["F"] - HYPER_TOL),
                    np.abs(sim["F"] - f_t))
                rms = float(np.sqrt(np.mean(err ** 2)))
                # branch-defect guard: the SIMULATED branch must actually
                # reproduce the three Freudenstein pairs (a solution whose
                # pairs are split across assembly branches is useless).
                precision = model.simulate(d, sample_theta, branch1=branch1, branch2=branch2)
                if not precision["ok"]:
                    continue
                pair_err = float(np.max(np.abs(precision["F"]-np.array([row[2] for row in samples]))))
                if pair_err > 1e-6:
                    continue
                mu_pen = max(0.0, MU_MIN - np.nanmin(sim["mu2"])) * D2R
                score = rms + 2.0 * mu_pen + 3.0 * pair_err
                if best is None or score < best[0]:
                    best = (score, d, branch2, rms, float(np.nanmin(sim["mu2"])))
    if best is None:
        raise RuntimeError("linkage 2: no Freudenstein seed passed assembly/Grashof")
    _, d, branch2, rms, mu = best
    return d, branch2, {"rms_F_deg": rms / D2R, "mu2_min_deg": mu}


# --------------------------------------------------------------------------
# Stage 3: joint optimisation
# --------------------------------------------------------------------------
KEYS = SOLVER["parameter_keys"]
BOUNDS = (SOLVER["lower_bounds"], SOLVER["upper_bounds"])
N_OPT = SOLVER["optimization_samples"]
_TH_OPT, _A_T, _F_T = targets.sample_targets(N_OPT)


def _residuals(x, branch1, branch2):
    d = dict(zip(KEYS, x))
    sim = model.simulate(d, _TH_OPT, branch1=branch1, branch2=branch2)
    if not sim["ok"]:
        return np.full(3 * N_OPT + 4, 8.0)
    r_alpha = (sim["alpha"] - _A_T) / (10 * D2R)
    down = _TH_OPT <= np.pi
    excess = np.maximum(0.0, sim["F"] - F_TOL) + np.maximum(0.0, -sim["F"] - HYPER_TOL)
    r_F = np.where(down, excess / (0.8 * D2R),
                   (sim["F"] - _F_T) / (8 * D2R))
    # hyperextension guard applies all cycle, not just the downstroke
    r_hyper = np.maximum(0.0, -sim["F"] - HYPER_TOL) / (0.8 * D2R)
    pen = [
        max(0.0, MU_MIN + 3 - np.nanmin(sim["mu1"])) / 2.0,
        max(0.0, MU_MIN + 3 - np.nanmin(sim["mu2"])) / 2.0,
        0.0 if grashof_crank_rocker(d["a1"], d["b1"], d["c1"], model.D1) else 2.0,
        0.0 if grashof_crank_rocker(d["a2"], d["b2"], d["c2"], model.L_IN) else 2.0,
    ]
    return np.concatenate([r_alpha, r_F, r_hyper, pen])


def optimise(design, branch1, branch2):
    lo, hi = BOUNDS
    x_seed = np.clip(np.array([design[k] for k in KEYS]), lo, hi)
    starts = [x_seed]
    for j, bump in ((7, 0.18), (8, -0.18), (3, 0.15)):  # eta / delta / kappa1
        x = x_seed.copy()
        x[j] = np.clip(x[j] + bump, lo[j], hi[j])
        starts.append(x)
    best = None
    total_nfev = 0
    for x0 in starts:
        x = x0
        for _ in range(2):  # warm restarts: each round polishes the last
            res = least_squares(_residuals, x, bounds=BOUNDS, args=(branch1, branch2),
                                x_scale="jac", max_nfev=SOLVER["max_nfev"], verbose=0,
                                ftol=1e-12, xtol=1e-12, gtol=1e-12)
            x, total_nfev = res.x, total_nfev + int(res.nfev)
        # select starts by screen violation + tracking error, not raw cost:
        # raw cost under-weights the two fold-band violations
        d = dict(zip(KEYS, x))
        rep = screen(d, branch1, branch2, n=180)
        if not rep.get("assembles_full_cycle"):
            score = 1e6
        else:
            score = (max(0.0, MU_MIN - rep["mu1_min_deg"]) + max(0.0, MU_MIN - rep["mu2_min_deg"])
                     + max(0.0, rep["max_F_downstroke_deg"] - F_TOL / D2R)
                     + max(0.0, -HYPER_TOL / D2R - rep["min_F_deg"])
                     + rep["rms_alpha_deg"] + rep["rms_F_upstroke_deg"])
        if best is None or score < best[1]:
            best = (x, score, float(res.cost))
    return dict(zip(KEYS, best[0])), {"cost": best[2], "nfev": total_nfev}


def _residuals_band(x, branch1, branch2):
    """Stage 3b residuals: fold-band compliance first, tracking second."""
    d = dict(zip(KEYS, x))
    sim = model.simulate(d, _TH_OPT, branch1=branch1, branch2=branch2)
    if not sim["ok"]:
        return np.full(4 * N_OPT + 2, 8.0)
    down = _TH_OPT <= np.pi
    band = np.where(down, (np.maximum(0.0, sim["F"] - F_TOL)
                           + np.maximum(0.0, -sim["F"] - HYPER_TOL)) / (0.5 * D2R), 0.0)
    hyper = np.maximum(0.0, -sim["F"] - HYPER_TOL) / (0.5 * D2R)
    track = np.concatenate([(sim["alpha"] - _A_T) / (15 * D2R),
                              np.where(down, 0.0, (sim["F"] - _F_T) / (12 * D2R))])
    pen = [max(0.0, MU_MIN + 2 - np.nanmin(sim["mu1"])),
           max(0.0, MU_MIN + 2 - np.nanmin(sim["mu2"]))]
    return np.concatenate([band, hyper, track, pen])


def band_polish(design, branch1, branch2):
    lo, hi = BOUNDS
    x0 = np.clip(np.array([design[k] for k in KEYS]), lo, hi)
    res = least_squares(_residuals_band, x0, bounds=BOUNDS, args=(branch1, branch2),
                        x_scale="jac", max_nfev=SOLVER["max_nfev"], verbose=0,
                        ftol=1e-12, xtol=1e-12, gtol=1e-12)
    return dict(zip(KEYS, res.x)), {"cost": float(res.cost), "nfev": int(res.nfev)}


# --------------------------------------------------------------------------
# Stage 4: screening
# --------------------------------------------------------------------------
def constrained_refine(design, branch1, branch2):
    """SLSQP with explicit sampled inequalities and a margin, not relaxed limits."""
    th, at, ft = targets.sample_targets(720)
    margin = SOLVER["safety_margin_deg"]*D2R
    def unpack(x):
        return dict(zip(KEYS, x))
    def objective(x):
        sim = model.simulate(unpack(x), th, branch1, branch2)
        if not sim["ok"]:
            return 1e8
        return float(np.mean(((sim["alpha"]-at)/(10*D2R))**2)+np.mean(((sim["F"]-ft)/(10*D2R))**2))
    def constraints(x):
        d = unpack(x)
        sim = model.simulate(d, th, branch1, branch2)
        # Keep fixed dimension even for invalid geometry.
        if not sim["ok"]:
            return np.full(5*len(th)+4, -100.)
        derivative = (np.roll(sim["alpha"],-1)-np.roll(sim["alpha"],1))/(4*np.pi/len(th))
        down = (derivative < 0) | (th <= np.pi)
        core=(np.degrees(th)>=SCREENS['core_downstroke_phase_deg'][0])&(np.degrees(th)<=SCREENS['core_downstroke_phase_deg'][1])
        limit=np.where(core,SCREENS['core_downstroke_fold_max_deg']*D2R,F_TOL)
        band = np.where(down, (limit-margin-sim["F"])/D2R, 100.)
        hyper = (sim["F"]+HYPER_TOL-margin)/D2R
        def geometry(a,b,c,g):
            return [b+c-g-a-0.01, g-abs(b-c)-a-0.01]
        return np.concatenate([band, hyper, sim["mu1"]-MU_MIN-0.3,
                               sim["mu2"]-MU_MIN-0.3, np.full(len(th),1.),
                               geometry(d["a1"],d["b1"],d["c1"],model.D1),
                               geometry(d["a2"],d["b2"],d["c2"],model.L_IN)])
    x0 = np.clip([design[k] for k in KEYS], *BOUNDS)
    result = minimize(objective, x0, method="SLSQP", bounds=list(zip(*BOUNDS)),
                      constraints={"type":"ineq", "fun": constraints},
                      options={"maxiter":250,"ftol":1e-10})
    return unpack(result.x), {"method":"SLSQP", "success":bool(result.success),
                              "message":str(result.message), "iterations":int(result.nit),
                              "margin_deg":SOLVER["safety_margin_deg"]}


def design_to_json(design, branch1, branch2):
    return {
        "optimized_design_deg_mm": {
            "linkage1_crank_a1_mm": design["a1"],
            "linkage1_coupler_b1_mm": design["b1"],
            "linkage1_rocker_c1_mm": design["c1"],
            "linkage1_ground_d1_mm": model.D1,
            "rocker1_offset_kappa1_deg": design["kappa1"] / D2R,
            "linkage2_crank_a2_mm": design["a2"],
            "linkage2_coupler_b2_mm": design["b2"],
            "linkage2_rocker_c2_mm": design["c2"],
            "linkage2_ground_d2_mm": model.L_IN,
            "elbow_offset_eta_deg": design["eta"] / D2R,
            "drive_phase_delta_deg": design["delta"] / D2R,
        },
        "assembly_branch": {"linkage1": branch1, "linkage2": branch2},
        "pivot_locations_flap_plane_mm": {
            "shoulder_S": [0.0, 0.0],
            "motor_O": list(model.O),
            "ground_line_angle_O_to_S_deg": model.GAMMA1 / D2R,
        },
    }


def main():
    print("Stage 1: Freudenstein seed, linkage 1 ...")
    d1only, br1, info1 = seed_linkage1()
    print("  ", info1)
    print("Stage 2: Freudenstein seed, linkage 2 (uses actual alpha) ...")
    d_seed, br2, info2 = seed_linkage2(d1only, br1)
    print("  ", info2)
    rep_seed = screen(d_seed, br1, br2)
    print("  seed screen passes:", rep_seed.get("passes"))
    print("Stage 3: joint optimisation ...")
    d_opt, info_opt = optimise(d_seed, br1, br2)
    print("  ", info_opt)
    rep_opt = screen(d_opt, br1, br2)
    print("Stage 3b: fold-band polish ...")
    d_pol, info_pol = band_polish(d_opt, br1, br2)
    print("  ", info_pol)
    rep_pol = screen(d_pol, br1, br2)
    print("  polished screen:", json.dumps(rep_pol, indent=1))
    print("Stage 3c: constrained full-cycle refinement ...")
    d_ref, refine_info = constrained_refine(d_pol, br1, br2)
    rep_ref = screen(d_ref, br1, br2)
    # choose by total screen violation + tracking error (lower is better);
    # all candidates are reported either way
    def viol(rep):
        if not rep.get("assembles_full_cycle"):
            return 1e6
        return (max(0.0, MU_MIN - rep["mu1_min_deg"]) + max(0.0, MU_MIN - rep["mu2_min_deg"])
                + max(0.0, rep["max_F_downstroke_deg"] - SCREENS["downstroke_fold_tol_deg"])
                + max(0.0, -SCREENS["hyperextension_tol_deg"] - rep["min_F_deg"])
                + rep["rms_alpha_deg"] + rep["rms_F_upstroke_deg"])
    cands = [(d_seed, rep_seed, "freudenstein_seed"),
             (d_opt, rep_opt, "optimised"),
             (d_pol, rep_pol, "optimised_band_polished"),
             (d_ref, rep_ref, "constrained_refined")]
    chosen, chosen_rep, label = min(cands, key=lambda c: (not c[1].get("passes",False), viol(c[1])))
    out = {
        "approach": "C",
        "chosen": label,
        **design_to_json(chosen, br1, br2),
        "input_digest": input_digest(),
        "inputs": input_snapshot(),
        "seed_geometry": design_to_json(d_seed, br1, br2),
        "seed_info": {"linkage1": info1, "linkage2": info2, "screen": rep_seed},
        "optimisation_info": {**info_opt, "screen": rep_opt},
        "band_polish_info": {**info_pol, "screen": rep_pol},
        "constraint_refinement_info": refine_info,
        "chosen_screen": chosen_rep,
    }
    outdir = str(OUTPUT_DIR)
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "dimensions.json"), "w") as f:
        json.dump(out, f, indent=2)
    print("Wrote outputs/dimensions.json — chosen:", label, "PASS" if chosen_rep["passes"] else "FAIL (inspect failed_checks)")


if __name__ == "__main__":
    main()
