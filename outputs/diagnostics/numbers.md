# Where the numbers come from

These are recomputed from the frozen parameter vector, not copied PASS flags.

| Link parameter | Saved value |
| --- | ---: |
| a | 14.770246 mm |
| b | 25.717150 mm |
| c | 30.969173 mm |
| aD | 15.426379 mm |
| h | 26.337039 mm |
| L | 143.084452 mm |

Canonical values and branches: `outputs/direct/dimensions.json`. Freeze guard: `config/presentation/frozen_design.json`.

| Reported quantity | Recomputed result |
| --- | --- |
| Shoulder minimum transmission | 40.500844° at crank 61.40° |
| Elbow minimum transmission | 40.500900° at crank 242.50° |
| Input travel | 360° per cycle |
| Nominal physical speed | 15 rpm from 60 / 4 seconds in config/build.json |
| Motion samples | 7200; 0.05° increments |

| Question | Source |
| --- | --- |
| Actual loop equations | `src/rmd/direct_drive.py:29` |
| Initial least-squares residuals | `src/rmd/direct_drive.py:48` |
| Hard refinement constraints | `src/rmd/direct_drive.py:58` |
| Transmission-angle calculation | `src/rmd/kinematics.py:27` |
| Desired angles | config/direct_drive.json → motion_targets; config/targets.json → samples; src/rmd/direct_targets.py |
| Final objective and solver | src/rmd/direct_drive.py → fit → cost; mean shoulder error² + 0.35 mean fold error² |
| Numerical package checks | outputs/direct/validation.json; outputs/single_face/validation.json |

## Reading the plots

Dashed motion curves are desired, solid curves are actual. The loss map varies only a and h, retaining the other eight parameters and both branches. Its white boundary, if present, outlines the sampled refinement constraints plus variable bounds. Blank regions fail closure. The gold star is the submitted geometry. This is a local sensitivity illustration, not proof of a global optimum or a new synthesized design. No physical collision audit is run for perturbed map points.

Lower loss alone is not a better machine: it can violate transmission, fold or size constraints. A thin feasible region may be missed by this coarse map. The same-face 3D variant remains a known collision experiment. No actuator has been selected, and 6.35 mm plywood has not been packaged.
