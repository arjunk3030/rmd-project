"""
Planar four-bar tools: Freudenstein synthesis and forward kinematics.

Conventions (standard Freudenstein form):
  ground link d from input pivot O to output pivot Q,
  crank a (input angle phi), coupler b, rocker c (output angle psi).
  phi and psi are measured from the O->Q ground-line direction.
  Loop closure gives, with K1 = d/a, K2 = d/c,
  K3 = (a^2 - b^2 + c^2 + d^2) / (2 a c):
      K1 cos(psi) - K2 cos(phi) + K3 = cos(phi - psi)
Three (phi, psi) pairs give three linear equations in (K1, K2, K3).
Lengths then follow once d (the scale) is chosen:
  a = d/K1, c = d/K2, b = sqrt(a^2 + c^2 + d^2 - 2 a c K3).
"""
import numpy as np


def freudenstein(pairs, d):
    """pairs: list of 3 (phi, psi) in radians (ground-line frame).
    d: ground length (sets the absolute scale).
    Returns dict(a, b, c, d) or None if no real four-bar fits."""
    M, rhs = [], []
    for phi, psi in pairs:
        M.append([np.cos(psi), -np.cos(phi), 1.0])
        rhs.append(np.cos(phi - psi))
    try:
        K1, K2, K3 = np.linalg.solve(np.array(M), np.array(rhs))
    except np.linalg.LinAlgError:
        return None
    if K1 <= 1e-9 or K2 <= 1e-9:
        return None
    a = d / K1
    c = d / K2
    b2 = a * a + c * c + d * d - 2.0 * a * c * K3
    if b2 <= 0:
        return None
    return {"a": float(a), "b": float(np.sqrt(b2)), "c": float(c), "d": float(d)}


def circle_intersection(c0, r0, c1, r1, branch, ref=None):
    """Point at distance r0 from c0 and r1 from c1.
    branch = +1/-1 picks the side; if ref is given, picks the intersection
    closest to ref (used for branch-continuous tracking)."""
    c0 = np.asarray(c0, float)
    c1 = np.asarray(c1, float)
    dv = c1 - c0
    dist = np.linalg.norm(dv)
    if dist < 1e-12 or dist > r0 + r1 or dist < abs(r0 - r1):
        return None
    ex = dv / dist
    x = (r0 * r0 - r1 * r1 + dist * dist) / (2.0 * dist)
    h2 = r0 * r0 - x * x
    if h2 < -1e-9:
        return None
    h = np.sqrt(max(h2, 0.0))
    ey = np.array([-ex[1], ex[0]])
    p_plus = c0 + x * ex + h * ey
    p_minus = c0 + x * ex - h * ey
    if ref is not None:
        return p_plus if np.linalg.norm(p_plus - ref) < np.linalg.norm(p_minus - ref) else p_minus
    return p_plus if branch > 0 else p_minus


def forward_fourbar(O, Q, a, b, c, phi, branch=1, ref=None):
    """One forward-kinematics step.
    O: input pivot (2,), Q: output pivot (2,), phi: input angle measured
    from the O->Q direction. Returns (rocker_tip B, output angle psi
    measured from the O->Q direction) or (None, None) if it cannot assemble.
    """
    O = np.asarray(O, float)
    Q = np.asarray(Q, float)
    ground_dir = Q - O
    gamma = np.arctan2(ground_dir[1], ground_dir[0])
    A = O + a * np.array([np.cos(gamma + phi), np.sin(gamma + phi)])
    B = circle_intersection(Q, c, A, b, branch, ref=ref)
    if B is None:
        return None, None
    psi = np.arctan2(*(B - Q)[::-1]) - gamma
    return B, float((psi + np.pi) % (2 * np.pi) - np.pi)


def transmission_angle(B, A, Q):
    """Angle (deg, 0..90) between coupler (B->A) and rocker (B->Q) at B."""
    v1 = np.asarray(A, float) - np.asarray(B, float)
    v2 = np.asarray(Q, float) - np.asarray(B, float)
    n1, n2 = np.linalg.norm(v1), np.linalg.norm(v2)
    if n1 < 1e-12 or n2 < 1e-12:
        return 0.0
    cosang = np.clip(np.dot(v1, v2) / (n1 * n2), -1.0, 1.0)
    ang = np.degrees(np.arccos(cosang))
    return float(min(ang, 180.0 - ang))


def grashof_crank_rocker(a, b, c, d, crank_is_input=True):
    """True if Grashof with the crank as the shortest link (so the input
    can rotate fully while the output only rocks)."""
    L = sorted([a, b, c, d])
    s, l = L[0], L[-1]
    if min(a, b, c, d) <= 0 or s + l >= sum([a, b, c, d]) - s - l - 1e-8:
        return False
    shortest_is_crank = abs(a - s) < 1e-9
    return bool(shortest_is_crank or not crank_is_input)
