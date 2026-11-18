# Project handoff — bat-wing mechanism

Updated November 4, 2026; scaled-design update November 17, 2026 (see the ×1.25 section at the end — the dimension tables below are the scaled values). This is a stationary Robot Mechanism Design class project. The immediate mock-up is **one wing** driven by **one motor**, with 3D-printed linkage parts, bearing/screw/nut pivots, and no fabric panels. The larger presentation concept has two mirrored wings and a bat silhouette.

## Current state and priorities

- The user wants a small, easy-to-understand, bat-like mechanism, ideally with one direct motor and no gears for the one-wing mock-up.
- **Do not change the submitted synthesis dimensions or motion without an explicit decision to redesign.** Earlier angle proposals were estimated aesthetic targets, not measurements from a real bat.
- The current one-wing **split-face direct-drive** visualization is a packaging concept, not a validated printable design. The solid inner-wing triangle is yellow; the two blue crank arms are rigidly connected to one input shaft. No second wing, belt, reversing gear or fabric is shown.
- The user wants practical results and short, clear updates; do not spend a long time silently forcing a packaging solution.

## Open the models

From the repository root:

```bash
open outputs/index.html                    # Website menu
open outputs/split_direct_3d.html          # Current one-wing mock-up concept
open outputs/direct_2d.html                # Six-bar, targets and wingtip trace
open outputs/direct_3d.html                # Original two-wing split-face design
open outputs/mockup_3d.html               # Same-face one-wing experiment (collision)
open outputs/offset_experiment_3d.html    # Offset-coupler experiment (collision)
```

`python3 run_all.py split-direct` regenerates the current one-wing view using saved poses. `python3 run_all.py demo` regenerates the presentation outputs. These commands do **not** run optimization or open a browser. They can overwrite generated files. The HTML views work locally without a server. MP4s are optional local exports under `outputs/videos/` and may not exist in a fresh clone; `python3 run_all.py video` requires FFmpeg. The existing 2D MP4 does not show the target overlay; the interactive 2D view does.

## Mechanism and synthesized geometry

Each wing is a **Stephenson six-bar**. Its two ternary links, common crank O–A–D and inner wing S–B–E, do not share a joint. The two blue crank arms are one rigid body through the common O shaft. O and S are fixed frame pivots; A, B, D, E and Q are moving joints; T is the wingtip. The shoulder four-bar O–A–B–S is a **Grashof Class I crank-rocker**: shortest + longest = 14.770 + 35.000 = 49.770 mm < 25.717 + 30.969 = 56.686 mm. Do not apply that four-bar classification to the whole six-bar.

All dimensions below are **joint center to joint center** and refer to the frozen direct design, not the older geared candidate.

| Quantity | mm |
| --- | ---: |
| Ground O–S | 35.000 |
| Shoulder crank O–A | 14.770 |
| Shoulder coupler A–B | 25.717 |
| Shoulder rocker S–B | 30.969 |
| Elbow crank O–D | 15.426 |
| Elbow coupler D–Q | 143.084 |
| Outer-wing output lever E–Q | 26.337 |
| Inner wing S–E | 125.000 |
| Outer wing E–T | 187.500 |

Crank O–A to O–D included angle is about 50.058°. For the inner triangle, B–S–E is about 67.278° and B–E is 116.591 mm. For the outer yellow L, Q–E–T is about 134.636° and Q–T is 206.855 mm. The model shows a rigid union of E–Q and E–T; T has no bearing hole. Full-precision parameters and branches are in `outputs/direct/dimensions.json`. Recompute from those saved values rather than rounding during calculations.

### CAD starting geometry

For the saved zero-input pose, use S = (0, 0), with the first coordinate outward and the second up (mm): O = (−10.00, −33.54), A = (4.45, −30.48), B = (26.13, −16.64), D = (−2.76, −19.91), E = (102.65, 71.33), Q = (86.36, 92.01), T = (288.98, 50.35). These are rounded reference positions, not manufacturing tolerances.

For flat CAD sketches, use S = (0, 0), E = (125, 0), B = (11.96, −28.56) for the yellow triangle; and E = (0, 0), T = (187.5, 0), Q = (−18.50, 18.74) for the outer L. Their zero-pose center planes along the shaft are A–B: −28.5; S–B–E: −22; O–A: −16; support plates: −9.5 and +9.5; O–D: +16; outer L: +18.5; D–Q: +27 mm. The resulting 40.5 mm E-plane separation is a serious unverified packaging tradeoff, not a finalized design.

### Motion and targets

Shoulder angle α is the inner wing relative to outward horizontal; positive is up. Elbow bend F is the outer-wing fold relative to the inner wing; 0° is straight. Target shoulder range is −30° to +35° and target fold 15°–70°. Targets were chosen to give a more extended downstroke and a larger mid-upstroke fold, not measured from animal footage.

The actual saved motion is approximately:

| Quantity | Result |
| --- | --- |
| Shoulder | −21.54° to +36.12°; 57.66° sweep |
| Downstroke elbow bend | 14.0°–39.5° |
| Upstroke elbow bend | 38.3°–65.0° |
| Nominal input | 360° per wingbeat; 15 rpm; 4 seconds/cycle |
| Minimum shoulder / elbow transmission angles | about 40.50° / 40.50° |

The original split-face design passed its **sampled nominal 3 mm-link** check with zero reported collisions at the original scale; the ×1.25 design does not (see the scale-up section at the end). It is not a validation of the newer 4 mm printed shapes, larger bearing bosses or the one-wing direct motor. `outputs/diagnostics/index.html` has target/actual curves, transmission plots and a local loss map; `motion_dense.csv` has 7,200 samples. The 2D dashed gray wing is the target, the solid wing is actual, and the purple path traces the actual wingtip.

## Synthesis and code

The current direct six-bar was sized **jointly** using bounded least squares followed by constrained SLSQP. The refinement uses actual rigid-loop closure and minimizes `mean((α − α_target)^2) + 0.35 * mean((F − F_target)^2)` in radians. Transmission, closure, fold and tracking requirements are separate constraints. This is numerical optimization, not two independent Freudenstein solutions. The earlier candidate used Freudenstein seeds.

| Location | Purpose |
| --- | --- |
| `src/rmd/direct_drive.py` | Current solver: `Problem.state`, `residual`, `constraints`, `fit`, and its nested final `cost` |
| `src/rmd/direct_targets.py`, `targets.py` | Estimated target curves and timing |
| `src/rmd/kinematics.py`, `fourbar.py` | Geometric closure and angle calculations |
| `config/direct_drive.json`, `config/targets.json` | Geometry, targets and constraints for the saved solve |
| `outputs/direct/dimensions.json` | Canonical saved solution and input snapshot |
| `src/rmd/legacy_geared_synthesis.py` | Older candidate; still needed when changed shared inputs require regenerating the historical reference |
| `src/rmd/split_direct.py`, `templates/mockup_geometry.js` | One-wing split-face visualization; not printable CAD |
| `optimization/README.md` | Main optimization source map and instructions |

The presentation guard in `config/presentation/frozen_design.json` checks protected inputs and code. To experiment without altering the submitted solution: `python3 run_all.py init-redesign NAME`, edit `experiments/NAME/config/`, then `python3 run_all.py redesign NAME`. New runs have timestamped outputs and may fail constraints. Do not update the frozen hashes merely to hide a change.

## Physical packaging: unresolved

The same-face layout has a real modeled collision: the A–B coupler crosses the D screw near 283.5°. The separate 20 mm offset-coupler experiment also fails: its return legs intersect D–Q and its ends still intersect D. Five simple layer swaps in `outputs/mockup/layer_checks.json` created other link/pin conflicts. These are limited sampled tests, not a proof that every possible offset is impossible.

The one-wing split-face concept separates the modeled D screw and A–B coupler axially by **39.5 mm**, but only selected envelopes have been screened; see `outputs/split_direct/clearance.json`. It has important design debts:

- Its inner wing and outer-wing center planes are **40.5 mm apart at E**, requiring an unusually long elbow shaft/spacers in the current depiction.
- Its two crank arms sit on opposite faces and must lock to the same shaft with the specified phase. The shaft, bearings, clamp method and frame support are schematic.
- The one-wing visualizations now draw the printed-part dimensions from `config/presentation/mockup.json`: 3.7 mm plate thickness, ~18 mm link width with Ø19 bosses (4.5 mm wall) around Ø10 bearing seats, MR106ZZ 6×10×3 bearings on 6 mm shaft pins with push-on clip retainers, and a Ø6 crank shaft bore. These match the current printed CAD; axial plane positions in the mock-up are still illustrative.
- The motor envelope is **14 mm diameter × 5 mm long**. No suitable motor has been identified in that tiny space. The original 3 mm package check cannot validate a real motor or new solid triangles.
- The attempted D-on-A-face rearrangement sends the D pin through the pictured fixed support plates at the zero pose.

A full solution needs actual selected bearings, screw heads/nuts and spacers, a realistic support and motor mount, and full-cycle solid/interference checks including the thickness of every printed part. Do not treat the rendered shapes as final STL/CAD or make a buildability claim from the current screen. Bearings must be supported correctly; spacers/retainers should avoid clamping moving parts against the frame.


## Website and delivery

`vercel.json` serves the committed `outputs/` directory as static files. Vercel **does not** run the optimizer or generate animations. Run locally, inspect, then commit and push updated outputs to redeploy. The landing page deliberately shows the split-face mock-up button, not the two newer failed mock-up experiment buttons; their local files remain available. Avoid exposing files accidentally: committed `outputs/` contents are public.

Use the repo README for setup and tests. As of this handoff, the only untracked file shown by Git was `Team13_synthesis.txt`; it appears to be a class submission pointer and should not be removed without checking with the user.


## Top-mounted drive concept for the two-wing views

The full split-face `direct_3d.html` and same-face `single_face_3d.html` now show one top-mounted motor driving an **18-tooth module-1 pinion** into the existing **34-tooth right-wing gear**. The second 34-tooth gear reverses the other wing. The external reduction from motor pinion to wing shaft is **34:18 ≈ 1.89:1**; any internal motor gearbox is additional. The old remote motor and belt are removed from those two visualizations. The separate one-wing split-face mock-up remains gearless.

A 720-pose preliminary envelope screen found no new drive/link/panel conflicts and sampled tooth vertices showed no penetration. It is not a full mesh, structural, tolerance, gear-strength or motor-selection validation. The same-face A–B/D collision is unaffected. The concept uses a 40 × 20 × 20 mm unselected motor envelope, a long shaft from the pinion at x = −4 mm to the motor face at x = +34 mm, and an added 10 mm rear support-plate bearing hole. Motor bracket, shaft bending, retention, wiring, real motor fit, total body depth and loaded operation remain unverified. The old baseline torque estimate does not establish motor requirements for this new gear train.

Settings: `config/presentation/top_motor.json`; implementation: `src/rmd/top_drive.py`; limited checks and assumptions: `outputs/top_motor/{split,same}/`. Regenerate just those two visualizations and checks with `python3 run_all.py top-drive`. The motor gear moves opposite the right wing gear; the other wing gear turns opposite the right gear.

## ×1.25 scale-up (November 17, 2026)

At Arjun's direction the frozen design was uniformly scaled ×1.25 to match the printed CAD parts (his Pin1/Pin2/coupler/rod hole spacings measure exactly 1.25× the old frozen lengths) and the design was **refrozen**: `config/direct_drive.json`, `config/direct_seed.json`, the saved parameters in `outputs/direct/dimensions.json`, and the lock in `config/presentation/frozen_design.json` all carry the scaled values (saved-package input digest `34da216f…`). Every link length, the ground (28 → 35 mm) and both wing segments (100/150 → 125/187.5 mm) scaled; angles, phases, branches and the motion are unchanged (shoulder −21.54° to +36.12°, fold 14.0°–65.0°, transmission minima 40.50°/40.50° — identical to the original). Shoulder spacing went 50 → 54 mm (not 62.5) so O stays at exactly 1.25× its old position relative to S while the 34 mm gear mesh (O-to-O) is preserved. The bat-face cover scaled to 92.5 × 100 mm and the body caps to 95/100/100 mm. Axial plane positions were deliberately NOT scaled; they are set by the hardware stack.

Stand adjustments forced by the lower scaled O: the common bearing plates grew to 52 mm tall (center z = −16) so the O bearing hole keeps its edge ligament, the stand legs were resized to meet the plate bottom and the base exactly (113 mm, center z = −98.5), and the base center dropped to z = −159 so the belt-hung actuator reservation clears it.

**Open issue — centerline interference at the new scale.** The scaled direct package no longer passes nominal validation: 21 modeled conflicts, all between the two wings' mirrored hardware at the shared front/rear planes. The A-joint parts (crank, coupler, pin, fasteners) clash around θ ≈ 144–168° and the D-joint parts around θ ≈ 118°; worst overlap 3.0 mm, minimum clearance −3.0 mm. Cause: the links reach 25% further inward while the O shafts stay 34 mm apart, so the mirrored A points pass ~4.5 mm apart laterally (was ~10.4 mm) and the D points ~3.1 mm (was ~9.3 mm). Motion, hardware and load checks all still pass. Consequences: `python3 run_all.py demo` now stops at its validation gate, and `test_both_complete_designs_recompute_checks` in `tests/test_synthesis.py` fails on the direct design until this is resolved. All presentation outputs were regenerated with the individual commands (`mockup`, `mockup-offset`, `split-direct`, `top-drive`, `diagnostics`, `video`) and reflect the scaled design; the direct validation status shown is the honest FAIL above. The fix is an axial-spacing decision (stagger the two wings' front/rear stacks, as the rear already is via `left_layer_spread_mm`, or match the stations used in the printed CAD) — Arjun's next pass. All other tests pass, including the four node viewer checks and the top-drive checks (0 gear conflicts at the scaled geometry).

The one-wing mock-up viewers were also restyled to the printed parts (see the packaging bullet above and `config/presentation/mockup.json`); support-plane and motor positions in the mock-up are still the old illustrative values pending the same spacing pass.
