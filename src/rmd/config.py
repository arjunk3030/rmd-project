"""Load editable assumptions; 'fixed' means held constant during this run only."""
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = Path(os.environ.get('RMD_CONFIG_DIR', ROOT / 'config')).resolve()
OUTPUT_DIR = Path(os.environ.get('RMD_OUTPUT_DIR', ROOT / 'outputs')).resolve()

def _load(name):
    return json.loads((CONFIG_DIR / f'{name}.json').read_text())

FIXED = _load('layout')
_TARGETS = _load('targets')
ESTIMATED_SAMPLES = _TARGETS['samples']
FREUDENSTEIN_SAMPLE_IDX = _TARGETS['freudenstein_sample_indices']
SCREENS = _load('requirements')
SOLVER = _load('solver')
BUILD = _load('build')


def input_snapshot():
    return {name: _load(name) for name in ('layout', 'targets', 'requirements', 'solver', 'build')}


def input_digest():
    return hashlib.sha256(json.dumps(input_snapshot(), sort_keys=True).encode()).hexdigest()


def validate():
    import numpy as np
    rows = np.asarray(ESTIMATED_SAMPLES, dtype=float)
    if rows.ndim != 2 or rows.shape[1] != 3 or len(rows) < 4 or not np.isfinite(rows).all():
        raise ValueError('targets.samples must contain finite [t/T, alpha_deg, fold_deg] rows.')
    if rows[0, 0] != 0 or rows[-1, 0] != 1 or np.any(np.diff(rows[:, 0]) <= 0):
        raise ValueError('Sample times must increase strictly from 0 to 1, including both endpoints.')
    if not np.allclose(rows[0, 1:], rows[-1, 1:], atol=1e-10, rtol=0):
        raise ValueError('Periodic target endpoints must have identical angles.')
    if FIXED['drive_sign'] not in (-1, 1) or FIXED['drive_ratio'] != 1:
        raise ValueError('This implementation supports a 1:1 drive, sign +1 or -1 only.')
    if FIXED.get('panel_style') not in ('tapered','rectangular'):
        raise ValueError('panel_style must be tapered or rectangular.')
    if not -30 <= FIXED.get('panel_pitch_deg',0) <= 45:
        raise ValueError('Panel pitch outside the supported prototype range.')
    if BUILD['motor_count']!=1:
        raise ValueError('motor_count must be1 for the current single-motor transmission.')
    if min(FIXED['inner_length_mm'], FIXED['outer_length_mm']) <= 0:
        raise ValueError('Wing lengths must be positive.')
    if np.linalg.norm(FIXED['motor_offset_mm']) <= 0:
        raise ValueError('Motor and shoulder must be distinct pivots.')
    for indices in FREUDENSTEIN_SAMPLE_IDX.values():
        if len(indices) != 3 or len(set(indices)) != 3 or any(i < 0 or i >= len(rows)-1 for i in indices):
            raise ValueError('Each Freudenstein seed needs three distinct non-endpoint-duplicate sample indices.')
    if SCREENS['downstroke_fold_tol_deg'] < 0 or SCREENS['hyperextension_tol_deg'] < 0:
        raise ValueError('Fold tolerances must be nonnegative.')
    if not 0 < SCREENS['mu_min_deg'] < 90:
        raise ValueError('Transmission-angle threshold must be between 0 and 90 degrees.')

validate()
