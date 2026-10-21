# Optimization

Start with **direct_drive.py**. This folder groups the main sources and inputs using symbolic links to their canonical files. There is only one copy of each file; the working Python package remains in `src/rmd/`. This is a navigation folder, not a standalone package to copy or submit by itself.

| File | Role |
| --- | --- |
| `direct_drive.py` | `Problem.state`: loop closure and actual motion; `Problem.residual`: initial fit errors; `Problem.constraints`: mechanical limits; `fit`: least squares followed by SLSQP; nested `cost`: final tracking loss. |
| `direct_targets.py` | Scales the timing curves into the desired shoulder and elbow motion. |
| `targets.py` | Interpolates the underlying target samples. |
| `kinematics.py` | Circle intersections and transmission-angle calculations. |
| `direct_drive.json` | Targets, geometry, parameter bounds and solver settings for the saved design. |
| `direct_seed.json` | Initial numerical guess and assembly branches. |

The final objective, evaluated with actual rigid-link closure, is:

`J = mean((shoulder − shoulder_target)²) + 0.35 mean((fold − fold_target)²)`

Angles are in radians. Hard constraints are separate from this objective. The first least-squares stage uses a different residual vector; see `Problem.residual` for its length mismatch, shoulder error and penalties.

## Run with changed inputs

From the repository root:

```bash
python3 run_all.py init-redesign my-bat
# Edit experiments/my-bat/config/direct_drive.json, not the frozen inputs here.
python3 run_all.py redesign my-bat
```

The runner snapshots inputs and writes new results under `experiments/my-bat/runs/<timestamp>/`. Its implementation is `src/rmd/redesign.py` and `redesign_worker.py`. The default `python3 run_all.py demo` uses the submitted solution and never optimizes.

Do not edit the input links here to explore a new design: they point to the frozen submitted inputs. Use the experiment copies. Editing a linked source also edits its canonical file.

## Legacy reference solver

`src/rmd/legacy_geared_synthesis.py` sizes the older geared candidate, using Freudenstein seeds followed by numerical refinement. It does **not** optimize the chosen direct six-bar. It remains a dependency only for rebuilding the historical reference after shared inputs change. It is not called during frozen demo generation.

## Other dependencies

These main files are not sufficient on their own. The current solver imports configuration/loading (`config.py`, `design_io.py`), shared reference calculations (`model.py`, `fourbar.py`) and geometry (`compact_drive.py`, `direct_package.py`, `assembly.py` and their helpers). The redesign workflow invokes `legacy_geared_synthesis.py` when changed shared inputs require regenerating its historical reference. Keep those modules in the package.

The templates, videos, landing page and Vercel configuration do not optimize the mechanism. After optimization, the runner separately invokes validation and visualization code. For a runnable submission, include the repository's `src/`, `config/`, required saved JSON files, `run_all.py` and dependencies rather than this navigation folder alone.
