"""Periodic, shape-preserving interpolation; no invented spline overshoot."""
import numpy as np
from scipy.interpolate import PchipInterpolator
from .config import ESTIMATED_SAMPLES


def _build():
    rows = np.asarray(ESTIMATED_SAMPLES, float)
    # Tile without duplicate cycle boundaries; evaluate only in the middle cycle.
    t = np.concatenate([rows[:-1, 0]-1, rows[:-1, 0], rows[:, 0]+1]) * 2*np.pi
    values = np.concatenate([rows[:-1, 1:], rows[:-1, 1:], rows[:, 1:]], axis=0)
    return PchipInterpolator(t, np.radians(values), axis=0)

_CURVE = _build()

def alpha_target(theta):
    return float(_CURVE(np.mod(theta, 2*np.pi))[0])

def F_target(theta):
    return float(_CURVE(np.mod(theta, 2*np.pi))[1])

def sample_targets(n=25):
    th = np.linspace(0, 2*np.pi, n, endpoint=False)
    values = _CURVE(th)
    return th, values[:, 0], values[:, 1]
