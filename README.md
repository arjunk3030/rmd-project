# Bat mechanism — final animation demo

Four views of the saved Stephenson six-bar. **Generating these demos never runs synthesis or changes link lengths.** The split-face layout is the chosen design; the same-face layout is a packaging experiment with known interference.

## Open or regenerate

From this folder, open the existing offline demo:

```bash
open outputs/index.html
```

To regenerate all four views and the evidence plots (Python 3.10+):

```bash
python3 -m pip install -r requirements.txt
python3 run_all.py demo
open outputs/index.html
```

No server, internet connection or JavaScript packages are needed. The HTML files contain their motion data. Keep `outputs/` together to preserve navigation. To share just one animation, its HTML file works independently.

| View | File | What it shows |
| --- | --- | --- |
| Same face | `outputs/single_face_3d.html` | Both crank arms on one face; rigid-body shading. Known coupler/pin interference remains. |
| Split faces | `outputs/direct_3d.html` | Chosen mechanism, with the two loops distributed across depth layers. No bat face. |
| Planar linkage | `outputs/direct_2d.html` | Right-wing six-bar, named joints, rigid triangles, target overlay and loop highlighting. |
| Bat appearance | `outputs/bat_3d.html` | Same motion with dark fabric and a cartoon body; structure initially hidden. Costume clearance is unverified. |

In 3D, drag to orbit, scroll to zoom, pause/scrub the crank, or choose the front view. Labels start off. The shoulder-only selector is an explanatory isolation, not another synthesized design. Panel shape/pitch controls change the appearance preview only. In 2D, the dashed gray wing is the desired pose; colored links are the actual solution. Triangle edges indicate rigid relationships, not additional stock to cut.

### Other commands

```bash
python3 run_all.py validate          # Recompute nominal package checks
python3 run_all.py diagnostics       # Motion plots, source map and loss landscape
python3 run_all.py video             # Export all four MP4s; needs ffmpeg on PATH
python3 run_all.py video --view 2d    # Or direct, single_face, bat
python3 -m unittest discover -s tests -v
node tests/check_viewer.cjs
```

Videos and posters go in `outputs/videos/`. They use the same embedded solved poses; they are fixed-camera exports rather than recordings of browser controls. `demo` does not encode movies. `all`, `direct` and `render` are compatibility aliases for demo generation; `--no-video` is accepted. Old `compact` and `--refit` commands are deliberately absent from this presentation entry point.

The same-face clearance FAIL is expected and reported, not hidden. A failure of the chosen split-face package stops normal demo generation. `build_ready` remains false: nominal checks are not hardware certification.

## Where a number comes from

Start with [generated numbers and code locations](outputs/diagnostics/numbers.md). Its line references point to the actual calculation functions. Machine-readable values are in `numbers.json`, with 7,200 full-cycle samples in `motion_dense.csv`.

| Quantity | Authoritative source | Meaning |
| --- | --- | --- |
| Final lengths and mounting phases | `outputs/direct/dimensions.json` → parameters | Saved synthesis results; lengths in mm, vector angles in radians. |
| Parameter order | `config/direct_drive.json` → parameter_names | Maps every vector entry to its symbol. `horn` means outer-wing output lever; `rod` means elbow coupler. |
| Shoulder/fold targets | `config/direct_drive.json` → motion_targets; `config/targets.json`; `src/rmd/direct_targets.py` | Estimated aesthetic targets and shared timing curve, not measured bat data. |
| Fixed body/wing geometry | `config/direct_drive.json`; `src/rmd/direct_package.py` | 28 mm ground, 50 mm shoulders, 34 mm input shafts, 100/150 mm wing segments. Held fixed during the final solve. |
| Transmission requirement | `config/direct_drive.json`; `Problem.constraints` | 40° acceptance; 40.5° refinement margin. |
| Actual minimum transmission | `outputs/diagnostics/numbers.json`; `kinematics.effective_angle` | Computed from solved coupler/output directions across the cycle, not a specified angle. |
| Input rotation and speed | `config/build.json`; crank sampling in `direct_drive.py` | 360° per wingbeat; nominal 4 seconds/cycle = 15 rpm. No actuator model selected. |
| Stock, loads and clearances | `config/build.json`, `config/direct_drive.json`; `outputs/direct/validation.json` | Assumptions and nominal checks, not measured material properties. |
| Alternate depth layers | `config/single_face.json`; `src/rmd/single_face.py` | Same in-plane synthesis, different physical packaging. |
| Playback and MP4 settings | `config/presentation/display.json` | Presentation-only inputs: cycle seconds, DPI and bitrate. |
| Cosmetic bat | `src/rmd/bat_preview.py`; `templates/viewer.html` | Outline, details and colors; does not change kinematics. |

The frozen direct lengths, rounded for reading, are:

| Loop component | Length (mm) |
| --- | ---: |
| Shoulder crank a1 | 11.816197 |
| Shoulder coupler b1 | 20.573720 |
| Shoulder rocker c1 | 24.775338 |
| Elbow crank a2 | 12.341103 |
| Outer-wing output lever h | 21.069631 |
| Elbow coupler L | 114.467562 |

Use the JSON's full precision for calculations. These are the current direct six-bar values; earlier geared-candidate values in the report are a different candidate.

### Safe input changes for this demo

Edit `config/presentation/display.json` to change playback speed or video quality, then regenerate. Changing playback speed does **not** recompute physical loads at that speed. Colors and cosmetic silhouette can be edited in the presentation sources listed above.

`config/presentation/frozen_design.json` records exact saved parameters and SHA-256 hashes of the physical inputs, canonical dimensions and core direct geometry/synthesis files. The entry point checks them before and after running. If a protected file changes, it stops with the file names rather than silently refitting. Restore the protected files to reproduce the submitted design. Do not update hashes to conceal a geometry change. A future redesign belongs in a separate copy with an intentional new synthesis and validation workflow. Environment overrides `RMD_CONFIG_DIR` and `RMD_OUTPUT_DIR` are rejected by the frozen demo.

“Fixed” means held constant in a solve; it does not mean a number is experimentally established. Targets, material assumptions and packaging dimensions were design choices. They are now locked to preserve the submitted results.

## Synthesis math and flow

The direct design was sized by **coupled numerical optimization**, not by independently solving two four-bars. The historical geared candidate used Freudenstein seeds; that does not make the final direct six-bar a standalone Freudenstein solution. See `src/rmd/direct_drive.py`: `Problem.state`, `Problem.residual`, `Problem.constraints`, and `fit`.

Let u(t) = (cos t, sin t). Ground pivots O and S are fixed. The common input rotates through θ:

- A = O + a1 u(θ + phase_A), D = O + a2 u(θ + phase_B).
- B lies at the intersection of circles centered at A and S with radii b1 and c1. The saved shoulder assembly branch selects the intersection.
- Shoulder angle α comes from the rocker angle plus its fixed mounting offset; E = S + 100 u(α).
- Q lies at the intersection of circles centered at E and D with radii h and L. The saved elbow branch selects the intersection. Q determines actual outer-wing orientation and fold F.

Both loops therefore share the same crank and moving inner wing. Counting rigid bodies gives ground O–S, crank O–A–D, coupler A–B, inner wing S–B–E, coupler D–Q and outer wing E–Q–T: six links. The two ternary links O–A–D and S–B–E do not share a joint, giving the Stephenson topology. The elbow loop cannot be treated as a second independent grounded four-bar.

The initial bounded least-squares fit asks whether a constant-length elbow coupler can reach the desired wing poses. With desired fold Ftarget:

`Qtarget = E + h u(α − Ftarget + η)`

`r_length = |Qtarget − D| − L`

`Problem.residual` combines this length mismatch, scaled shoulder error and mechanical penalties. SciPy's bounded least-squares method uses a numerical Jacobian; it is not plain fixed-step gradient descent. The elbow is included from the start. Computing the shoulder first locates the moving elbow E.

Final SLSQP refinement uses actual rigid-link closure and minimizes, in radians:

`J = mean((α − αtarget)²) + 0.35 mean((F − Ftarget)²)`

All ten lengths/phases are coupled optimization variables. The weight 0.35 sets the preference for elbow tracking relative to shoulder tracking. Separate inequality constraints enforce transmission margins, fold behavior, tracking limits and closure. SLSQP uses local derivative information to solve successive constrained subproblems; this is a numerical implementation choice, not a new linkage synthesis theorem. The final design compromises on estimated motion targets to retain workable transmission. Neither optimizer runs when generating the demo.

## Evidence plots and checks

Open `outputs/diagnostics/index.html`:

- **Motion and transmission:** desired versus actual shoulder/fold curves and both transmission angles over a revolution. Dense minima are about 40.501°, above the 40° acceptance limit.
- **Local loss landscape:** varies shoulder crank a1 and output lever h, holding the other eight parameters fixed. The star is the unchanged design. The white boundary, where visible, shows sampled numerical constraints and bounds. Blank regions fail closure. This is a sensitivity illustration, not re-optimization, a global-optimum proof or a collision-checked family of alternatives.

Physical package checks use 1,440 poses. The original split-face layout has zero nominal reported conflicts. The same-face variant retains the shoulder-coupler/elbow-crank-pin collision on both wings. The 2D projection collapses depth, so a crossing line alone does not establish a physical collision.

## Scope and build limitations

The passing package uses **3 mm stock**, not the planned ¼-inch (6.35 mm) plywood. Thin plastic film, actual mass, joint friction, fabric tension and loaded deflection still need physical verification. The costume is cosmetic. No real motor/servo, spline or control electronics have been selected; the reserved actuator envelope is only a placeholder. A limited-travel positional servo does not directly execute the modeled continuous crank rotation.

Load estimates are provisional. In particular, the legacy moving-mass calculation does not explicitly include the direct elbow-crank part under its `crank2_direct` name. This cleanup preserves those historical calculations rather than changing submitted numerical results; do not treat the torque output as a completed actuator-sizing calculation.

## Code and retained files

| Responsibility | Files under `src/rmd/` |
| --- | --- |
| Demo entry point and frozen-file check | `presentation.py`, `freeze.py`; root `run_all.py` |
| Saved design loading and build/check orchestration | `designs.py`, `design_io.py` |
| Direct synthesis, targets, geometry | `direct_drive.py`, `direct_targets.py`, `direct_package.py` |
| Same-face package | `single_face.py` |
| Loop closure and transmission | `kinematics.py`, `fourbar.py` |
| Physical checks | `validation.py`, `clearance.py`, `checks.py`, `loads.py` |
| 3D/2D presentation | `build_viewer.py`, `linkage2d.py`, `templates/` |
| Videos and explanatory plots | `demo_video.py`, `animate3d.py`, `diagnostics.py` |
| Historical candidate and shared backend | `model.py`, `synthesize.py`, `compact_drive.py`, `config.py` |

Obsolete compact/coaxial animation and fabrication outputs were removed. Historical candidate dimensions, validation records and solver/backend code remain because the report compares two candidates and the current implementation shares those modules. `outputs/direct/` and `outputs/single_face/` contain the current generated checks and reference geometry; they are not fabrication approval. Existing report material is retained in `docs/design_freeze/`; this README is authoritative for the new demo commands.

## Explicit redesign mode: update inputs and optimize again

The default remains `python3 run_all.py demo`: saved dimensions, no optimization. To try new inputs without altering the submitted design:

```bash
python3 run_all.py init-redesign my-bat
# Edit experiments/my-bat/config/direct_drive.json (targets, bounds, geometry)
# Other copied config files are editable too.
python3 run_all.py redesign my-bat
```

The command prints the result folder:

```text
experiments/my-bat/runs/<UTC timestamp>/
  config/           exact input snapshot for this run
  run.log           optimizer and validation output
  run.json          status and Python/NumPy/SciPy versions
  outputs/
    index.html      four experimental animations
    direct/dimensions.json
    direct/synthesis_attempts.json
    direct/validation.json
```

Open the printed `outputs/index.html`. Edit the experiment's top-level `config/` and rerun `redesign my-bat` for another attempt; every attempt gets a new directory. The submitted `config/` and `outputs/` remain untouched. No automatic promotion to the final demo occurs. Keep or delete experiments independently of the final demo.

This explicitly calls the original bounded least-squares plus SLSQP pipeline, then recomputes full package validation. If shared reference inputs (`layout`, `targets`, `requirements`, `solver`, or `build`) changed, the historical reference synthesis runs first because the current backend depends on it. Changing only `direct_drive.json` does not rerun that reference solve. New inputs may produce no feasible solution or a physically colliding candidate; the command exits with an error and keeps the run log/results for inspection. Optimization success alone is not a package PASS. The same-face view retains inherited packaging warnings; consult its freshly computed validation for the new candidate.

Useful editable fields include `motion_targets`, `wing_lengths_mm`, `ground_mm`, `lower_bounds`, `upper_bounds`, and `random_seed` in the copied `direct_drive.json`. Shared assumptions such as stock thickness are in the copied `build.json`. Coupled constraints must stay consistent: increasing a requested sweep does not guarantee feasibility at the same transmission threshold and body size.

The optimizer uses a fixed configurable random seed. Identical inputs and software normally reproduce results, but changing a seed, bounds, algorithm or numerical-library version may produce another local solution. The snapshot and version record make comparisons traceable. The existing solver has internal iteration caps; run logs are written while it works, and Ctrl-C may stop an expensive exploration. This mode does not use the frozen-file guard on the experimental inputs; the parent command still checks the submitted design before and after the run.

Implementation: `src/rmd/redesign.py` creates snapshots and launches a fresh process; `redesign_worker.py` runs the existing numerical pipeline with isolated configuration and output paths.


## Environment and Git setup

For an isolated Python environment, run from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 run_all.py demo
```

Python 3.10+ is required for generation. Existing HTML demos need only a browser. `requirements.txt` is the single dependency list; `pyproject.toml` reads it too. Optional developer installation: `python3 -m pip install -e .` (editable checkout; keep the project config and outputs alongside the source). Version ranges are compatibility bounds, not an exact environment lock. This workflow was checked with Python 3.12.3; the experiment run record captures numerical-library versions for each redesign.

FFmpeg must be installed separately and available on PATH for MP4 export. Node.js is only needed for `node tests/check_viewer.cjs`. No npm installation, browser libraries, account or API key is needed.

`.gitignore` excludes virtual environments, Python/tool caches, local secrets, regenerated videos and experiment run directories. It intentionally keeps final HTML demos, saved dimensions, validation records, configuration, source and docs eligible for Git: the default demo depends on the saved JSON files. Experiment input folders remain eligible to commit. Ignore rules do not remove anything already tracked by Git. No Git repository was initialized or commits created by this setup.

### How the animations are implemented

The HTML/JavaScript templates are custom code in `src/rmd/templates/`, populated with solved Python motion data. HTML organizes the page and controls. JavaScript updates the drawing each frame. Canvas is a standard browser drawing API, not a separate installed animation application: our code projects 3D points onto the 2D canvas and draws the links and panels. The planar view uses SVG, another browser graphics format. These are standard web technologies; the mechanism renderer is custom, rather than a CAD or physics engine. MP4 exports use Matplotlib and FFmpeg.
