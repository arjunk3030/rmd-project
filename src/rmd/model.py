"""
Approach C mechanism model (one wing, in the flap plane).

Coordinates: 2D flap plane, (outboard, up), shoulder pivot S at origin.
  alpha : inner-wing angle from +outboard axis (rad, + up)
  F     : outer-wing fold relative to inner wing (rad, + folded down);
          outer wing absolute angle = alpha - F.

Linkage 1 (body frame): ground O->S (O = motor pivot, FIXED offset),
  crank a1 at O (angle = motor angle theta), coupler b1,
  rocker c1 at S whose lever direction = alpha + kappa1
  (kappa1 = rocker-to-wing mounting offset, OPTIMIZED).

Linkage 2 (inner-wing frame; origin S, x-axis along inner wing):
  ground S->E is the inner wing itself (length L_in, FIXED),
  crank a2 at S with frame angle u2 = DRIVE_SIGN*theta + delta - alpha
  (delta = drive phase, OPTIMIZED; ideal drive is 1:1),
  coupler b2 (the rod along the wing),
  elbow lever c2 at E whose frame direction v2 = eta - F
  (eta = elbow lever mounting offset, OPTIMIZED).

A design dict holds exactly the nine OPTIMIZED numbers:
  a1 b1 c1 kappa1 | a2 b2 c2 eta delta
"""
import numpy as np

from .config import FIXED
from .fourbar import circle_intersection, transmission_angle

S = np.array([0.0, 0.0])
O = np.array(FIXED["motor_offset_mm"], float)  # motor pivot, flap plane
D1 = float(np.linalg.norm(S - O))              # linkage-1 ground length
L_IN = float(FIXED["inner_length_mm"])
L_OUT = float(FIXED["outer_length_mm"])
GAMMA1 = float(np.arctan2(*(S - O)[::-1]))     # O->S ground-line angle
CRANK1_PHASE = np.radians(FIXED["crank1_phase_deg"])
# Ideal drive sign: +1 co-rotating, -1 counter-rotating.
# Direct equal gears implement -1:1 in the current physical assembly.
DRIVE_SIGN = float(FIXED.get("drive_sign", 1))


def _dir(ang):
    return np.array([np.cos(ang), np.sin(ang)])


def simulate(design, thetas, branch1=1, branch2=1):
    """Fixed signed-circle branches, vectorized over ascending crank angles.

    No nearest-neighbor branch switching is permitted. The chosen side of each
    circle intersection remains invariant, including at the cycle seam.
    """
    th = np.asarray(thetas, float)
    if th.ndim != 1 or not np.isfinite(th).all() or len(th) < 1:
        raise ValueError("thetas must be a nonempty finite 1D array")
    if np.any(np.diff(th) < 0):
        raise ValueError("thetas must be ascending for continuous unwrapping")
    if branch1 not in (-1, 1) or branch2 not in (-1, 1):
        raise ValueError("Assembly branches must be +1 or -1")
    def dirs(angles):
        return np.column_stack((np.cos(angles), np.sin(angles)))
    def intersections(center, radius, pins, rods, branch):
        dv = pins-center
        distance = np.linalg.norm(dv, axis=1)
        valid = (distance > 1e-10) & (distance <= radius+rods) & (distance >= abs(radius-rods))
        ex = dv / np.maximum(distance[:, None], 1e-15)
        along = (radius**2-rods**2+distance**2)/(2*np.maximum(distance, 1e-15))
        height2 = radius**2-along**2
        valid &= height2 >= -1e-8
        ey = np.column_stack((-ex[:, 1], ex[:, 0]))
        points = center + along[:, None]*ex + branch*np.sqrt(np.maximum(height2, 0))[:, None]*ey
        points[~valid] = np.nan
        return points, bool(valid.all())
    def mu(B, A, Q):
        v, w = A-B, Q-B
        cosang = np.sum(v*w, axis=1)/(np.linalg.norm(v,axis=1)*np.linalg.norm(w,axis=1))
        return np.degrees(np.arccos(np.clip(np.abs(cosang), 0, 1)))
    out = {"thetas": th, "ok": False, "ok1": False}
    A = O+design["a1"]*dirs(th+CRANK1_PHASE)
    B, ok1 = intersections(S, design["c1"], A, design["b1"], branch1)
    out.update(A1=A, B1=B, ok1=ok1)
    if not ok1:
        return out
    alpha = np.unwrap(np.arctan2(B[:, 1], B[:, 0]))-design["kappa1"]
    E = L_IN*dirs(alpha)
    out.update(alpha=alpha, E=E, mu1=mu(B,A,S))
    u2 = DRIVE_SIGN*th+design["delta"]-alpha
    P = design["a2"]*dirs(u2)
    Ef = np.array([L_IN, 0.0])
    Q, ok2 = intersections(Ef, design["c2"], P, design["b2"], branch2)
    def rotate(points):
        ca, sa = np.cos(alpha), np.sin(alpha)
        return np.column_stack((ca*points[:,0]-sa*points[:,1], sa*points[:,0]+ca*points[:,1]))
    out.update(u2=u2, P2=rotate(P), Q2=rotate(Q), mu2=mu(Q,P,Ef), ok=ok2)
    if ok2:
        fold = design["eta"]-np.unwrap(np.arctan2(Q[:,1], Q[:,0]-L_IN))
        out.update(F=fold, TIP=E+L_OUT*dirs(alpha-fold))
    return out
