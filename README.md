# Bat-wing mechanism

One actuator coordinates shoulder flapping and elbow folding through a **Stephenson six-bar per wing**. The saved design is used by default; optimization runs only when explicitly requested.

## View the animations

```bash
open outputs/index.html
```

| View | File in `outputs/` |
| --- | --- |
| Chosen split-face mechanism | `direct_3d.html` |
| Same-face packaging experiment | `single_face_3d.html` |
| 2D linkage with target overlay | `direct_2d.html` |
| Bat appearance | `bat_3d.html` |

The same-face package has a known collision. The chosen package passes nominal checks for **3 mm stock**; 6.35 mm plywood and actual actuator sizing remain unverified.

## Setup and generate

Python 3.10+:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 run_all.py demo
```

`demo` overwrites the existing animations and plots using saved dimensions. It does **not** optimize or open a browser.

| Command | Result |
| --- | --- |
| `python3 run_all.py validate` | Recheck the saved design |
| `python3 run_all.py diagnostics` | Motion, transmission and loss plots |
| `python3 run_all.py video` | Four MP4s in `outputs/videos/`; requires FFmpeg |

Existing HTML files need only a browser. For the presentation's target overlay, use the interactive 2D view; the 2D MP4 shows actual motion only.

## Optimization: start here

**[optimization/README.md](optimization/README.md)** groups the main files and explains their dependencies. Files in that folder are links to the originals, not duplicate implementations.

| File | Purpose |
| --- | --- |
| [`direct_drive.py`](src/rmd/direct_drive.py) | `state()` computes motion; `residual()` defines the initial fit; `constraints()` defines limits; **`fit()` runs optimization** |
| [`direct_targets.py`](src/rmd/direct_targets.py) | Desired shoulder and elbow curves |
| [`kinematics.py`](src/rmd/kinematics.py) | Link closure and transmission calculations |
| [`config/direct_drive.json`](config/direct_drive.json) | Targets, fixed geometry, bounds and solver settings |
| [`outputs/direct/dimensions.json`](outputs/direct/dimensions.json) | Final lengths, mounting phases and assembly branches |
| [`legacy_geared_synthesis.py`](src/rmd/legacy_geared_synthesis.py) | Older candidate's solver; still needed when redesign regenerates its reference |

The current six-bar is sized **jointly**, using bounded least squares followed by constrained SLSQP. The final objective is:

```text
J = mean((shoulder − shoulder_target)²)
    + 0.35 × mean((fold − fold_target)²)
```

Angles are in radians. Transmission, closure and motion limits are separate constraints. See [numbers and code locations](outputs/diagnostics/numbers.md) for result provenance, or [the synthesis explanation](docs/synthesis_explained.md) for more detail.

### Try different inputs

```bash
python3 run_all.py init-redesign my-bat
# Edit experiments/my-bat/config/direct_drive.json
python3 run_all.py redesign my-bat
```

Each run saves an input snapshot, log, new dimensions, validation and animations under `experiments/my-bat/runs/<timestamp>/`. Failed candidates remain available for inspection. The submitted design is untouched.

Edit the **experiment's** config files, not the frozen originals. The default demo checks protected files against `config/presentation/frozen_design.json` and refuses changed inputs rather than silently refitting.

## Presentation files

- `src/rmd/templates/` — landing page, 3D viewer and 2D viewer.
- `src/rmd/bat_preview.py` — cosmetic bat body.
- `config/presentation/display.json` — playback speed and video quality; changing playback does not validate new physical operating speeds.
- `docs/design_freeze/` — report sections and comparison candidate.

Edit templates, regenerate locally, then commit the updated outputs. Saved geometry and motion are independent of these presentation edits.

## Vercel

Import the Git repository with **Application Preset: Other**, root `./`. The included `vercel.json` sets output directory **`outputs`** and empty install/build commands.

**Vercel serves committed files only.** To update the site: generate locally → inspect → commit outputs → push. No Python or optimization runs during deployment. All committed files inside `outputs/` are public.

Git ignores environments, caches, videos and experimental runs. Keep the final HTML and saved JSON files tracked; the demo needs them.

## Checks

```bash
python3 -m unittest discover -s tests -v
node tests/check_viewer.cjs
```

Node.js is only needed for viewer tests. No npm packages are required.
