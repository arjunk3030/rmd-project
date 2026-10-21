"""Load the chosen design from outputs/dimensions.json as a model design dict."""
import json
import os

import numpy as np
from .config import OUTPUT_DIR, input_digest

D2R = np.pi / 180.0
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")


def load_design(allow_stale=False):
    with open(OUTPUT_DIR / "dimensions.json") as f:
        data = json.load(f)
    if not allow_stale and data.get("input_digest") != input_digest():
        raise ValueError("Shared inputs do not match the saved reference. Use the explicit redesign workflow to regenerate it.")
    dd = data["optimized_design_deg_mm"]
    design = {
        "a1": dd["linkage1_crank_a1_mm"], "b1": dd["linkage1_coupler_b1_mm"],
        "c1": dd["linkage1_rocker_c1_mm"], "kappa1": dd["rocker1_offset_kappa1_deg"] * D2R,
        "a2": dd["linkage2_crank_a2_mm"], "b2": dd["linkage2_coupler_b2_mm"],
        "c2": dd["linkage2_rocker_c2_mm"], "eta": dd["elbow_offset_eta_deg"] * D2R,
        "delta": dd["drive_phase_delta_deg"] * D2R,
    }
    br = data["assembly_branch"]
    return design, br["linkage1"], br["linkage2"], data
