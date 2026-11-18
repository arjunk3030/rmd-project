"""Draw the saved one-wing geometry and uniformly scaled center distances."""
from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "outputs" / ".matplotlib"))

import matplotlib.pyplot as plt
import numpy as np

from rmd.designs import get_direct
from rmd.direct_drive import Problem

v, shoulder_branch, elbow_branch, _ = get_direct(allow_fit=False)
problem = Problem(1440)
sim = problem.state(v, shoulder_branch, elbow_branch)["simulation"]
points = {"O": np.asarray(problem.O), "S": np.zeros(2)}
for name, key in [("A", "A1"), ("B", "B1"), ("D", "P2"), ("E", "E"), ("Q", "Q2"), ("T", "TIP")]:
    points[name] = np.asarray(sim[key][0])

rows = [
    ("O–S", "Fixed pivot spacing", "#64748b"),
    ("O–A", "Shoulder crank", "#2563eb"),
    ("O–D", "Elbow crank", "#2563eb"),
    ("A–D", "Crank pin spacing", "#2563eb"),
    ("A–B", "Shoulder coupler", "#2563eb"),
    ("S–B", "Shoulder triangle", "#c69206"),
    ("S–E", "Inner wing / triangle", "#c69206"),
    ("B–E", "Shoulder triangle", "#c69206"),
    ("D–Q", "Elbow coupler", "#f07816"),
    ("E–Q", "Outer L: short arm", "#d24a43"),
    ("E–T", "Outer L: wing", "#d24a43"),
    ("Q–T", "Outer L: reference only", "#d24a43"),
]
lengths = [float(np.linalg.norm(points[x[0]] - points[x[-1]])) for x, _, _ in rows]

fig = plt.figure(figsize=(13, 8.5), facecolor="white", layout="constrained")
gs = fig.add_gridspec(2, 2, height_ratios=[1, 1.4], width_ratios=[1, 1])
fig.suptitle("One wing · linkage dimension map", fontsize=20, fontweight="bold")

def draw(ax, close=False):
    def line(a, b, color, width=3, style="-"):
        p, q = points[a], points[b]
        ax.plot([p[0], q[0]], [p[1], q[1]], style, color=color, lw=width, solid_capstyle="round")
    line("O", "S", "#64748b", 2, "--")
    for a, b in [("O", "A"), ("O", "D"), ("A", "B")]: line(a, b, "#2563eb")
    for a, b in [("S", "B"), ("B", "E"), ("E", "S")]: line(a, b, "#d6a110")
    line("D", "Q", "#f07816")
    for a, b in [("E", "Q"), ("E", "T")]: line(a, b, "#d24a43")
    for name, xy in points.items():
        ax.scatter(*xy, s=35, facecolors="white", edgecolors="#152238", zorder=5)
        offsets = {"O":(-12,-14),"A":(4,-15),"D":(-18,4),"S":(-12,6),"B":(5,-8),"E":(5,-12),"Q":(-14,6),"T":(5,0)}
        ax.annotate(name, xy, xytext=offsets[name], textcoords="offset points", fontweight="bold", fontsize=10)
    ax.set_aspect("equal"); ax.axis("off")
    if close: ax.set_xlim(-23, 32); ax.set_ylim(-39, 13)
    else: ax.set_xlim(-25, 250); ax.set_ylim(-45, 95)

ax = fig.add_subplot(gs[0, 0]); draw(ax); ax.set_title("Full wing · one pose (not a cut pattern)", loc="left", fontsize=11)
ax = fig.add_subplot(gs[0, 1]); draw(ax, True); ax.set_title("Enlarged body and crank area", loc="left", fontsize=11)
ax = fig.add_subplot(gs[1, :]); ax.axis("off")
data = [[key, desc] + [f"{length * scale:.2f}" for scale in (1, 1.25, 1.5)] for (key, desc, _), length in zip(rows, lengths)]
table = ax.table(cellText=data, colLabels=["Centers", "Part / reference", "Current ×1", "+25% ×1.25", "+50% ×1.5"], cellLoc="left", colLoc="left", loc="center", colWidths=[.12,.40,.16,.16,.16])
table.auto_set_font_size(False); table.set_fontsize(10); table.scale(1, 1.48)
for (row, col), cell in table.get_celld().items():
    cell.set_edgecolor("#dce3ea")
    if row == 0: cell.set_facecolor("#e9eef3"); cell.get_text().set_fontweight("bold")
    elif row % 2 == 0: cell.set_facecolor("#f7f9fb")
    if row > 0 and col == 0: cell.get_text().set_color(rows[row-1][2]); cell.get_text().set_fontweight("bold")
fig.text(.5, .008, "All values: millimeters, center-to-center (T is a tip). O–S, A–D and Q–T are reference distances, not added links. Uniform scaling preserves angles.", ha="center", fontsize=9)
out = ROOT / "outputs" / "diagrams"
out.mkdir(parents=True, exist_ok=True)
for ext in ("svg", "pdf", "png"):
    fig.savefig(out / f"scaled_linkage_dimensions.{ext}", dpi=180, bbox_inches="tight")
print("Wrote scaled linkage dimension map (SVG, PDF, PNG).")
