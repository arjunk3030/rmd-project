# Bat wing mechanism project handoff

Updated 20 October 2026. Workspace: `/Users/arjun/Documents/code/School/RMD/rmd-project`.

## Current state

The project is a stationary, single-actuator bat-like flapping mechanism for Robot Mechanism Design. The preferred working model is the **direct Stephenson six-bar**, mirrored once for each wing. Its saved motion and original 3 mm stock package pass the nominal numerical checks. It is not a completed fabrication design.

**The latest confirmed material choice is ¼-inch plywood links and thin plastic film over the wing frame. The physical model still uses 3 mm links. Updating the package to 6.35 mm stock is outstanding.** No actuator model has been selected.

A separate same-face packaging experiment exists, but it fails collision checks. Do not replace the original passing model with that experiment or describe it as buildable.

## User intent and priorities

- The central body must remain small enough for the whole mechanism to look like a bat.
- Use one actuator for both wings and mechanically coordinate shoulder flap with elbow folding.
- Keep at least 40° transmission angle throughout the motion; this takes priority over exact target angles.
- Angles and dimensions originally proposed were estimates and may change for a practical design.
- Use laser-cut plywood links and thin plastic-film wing coverings. Keep realistic fasteners, supports and clearances in view.
- Preserve the mechanical model, the simplified 2D explanation, and the separate bat appearance preview.
- Explain synthesis and rigid-link counting plainly. The user wants an identifiable method from the course sheet.
- Keep experiments isolated. Report serious downsides promptly instead of spending a long time silently trying to force a solution.

## Which version to open

Run from the workspace root:

```bash
open outputs/direct_3d.html
open outputs/direct_2d.html
open outputs/bat_3d.html
open outputs/single_face_3d.html
open outputs/compact_3d.html
```

| File | Purpose and status |
| --- | --- |
| `outputs/direct_3d.html` | Original direct mechanical package. Bat face hidden and cover control removed from this view. Nominal clearance PASS for the saved 3 mm package. |
| `outputs/direct_2d.html` | One wing projected into its motion plane, with joint labels, shaded rigid triangles, loop highlights, playback and a shoulder close-up. Colors match the mechanical 3D view. |
| `outputs/bat_3d.html` | Separate cartoon bat body, ears, tail, eyes and fangs, with dark plum wings. Same wing motion; drive hidden initially. Cosmetic silhouette is not clearance-validated. |
| `outputs/single_face_3d.html` | Experimental same-face layout with common V-crank. Motion preserved, clearance FAIL. |
| `outputs/compact_3d.html` | Older geared comparison, retained. It is not the preferred direct six-bar package. |

The original small face geometry is still present in the direct package configuration and clearance audit even though it is no longer drawn in the mechanical viewer. This differs from the larger cartoon costume, which is an appearance-only addition.

## Mechanism and link counting

Each wing is one Stephenson six-bar, not two independent four-bars. Count rigid bodies, not separate pieces of wood:

| Link | Rigid body |
| --- | --- |
| 1 | Body/frame joining fixed pivots O and S |
| 2 | Input shaft and both crank arms, carrying O, A and D |
| 3 | Shoulder connecting rod A–B |
| 4 | Shoulder rocker and inner wing, carrying S, B and E |
| 5 | Elbow connecting rod D–Q |
| 6 | Outer wing and its horn, carrying E and Q; T is the wingtip |

The original shoulder four-bar is O–A–B–S–O. Adding the rod D–Q and outer wing Q–E adds a two-link dyad. Both crank arms are rigidly locked to the shaft, so they remain one link even when mounted in different depth planes.

The ternary links O–A–D and S–B–E do not share a pivot directly, making this a **Stephenson** chain. The shaded triangles mean fixed geometry within a moving rigid body; they are not fixed to the frame and do not require triangular plates. Only O and S are fixed pivots. Six links with seven revolute joints give planar mobility M = 3(6−1)−2(7) = 1.

The shoulder four-bar is a **Grashof Class I crank–rocker**: shortest + longest = 11.816 + 28 = 39.816 mm, less than 20.574 + 24.775 = 45.349 mm. The crank is shortest and adjacent to ground. Do not apply ordinary four-bar Grashof classification separately to the moving-ground elbow loop or to the entire six-bar.

## Synthesis method

The final direct design uses **joint numerical optimization**, following Part 4 of the course sheet and the six-bar extension in §5.5. It is not a final three-position Freudenstein solution. The older geared design did use Freudenstein seeds.

For every candidate, analysis proceeds shoulder first, then elbow, because the shoulder determines the elbow location. This is a calculation dependency, not two independent synthesis stages. The optimizer can change both sections together.

1. Build desired shoulder and elbow curves over motor angle.
2. Choose a candidate vector of six lengths and four mounting/phase angles.
3. Solve the shoulder circle closure and locate elbow E.
4. Initial bounded least squares places the horn at the desired bend and penalizes deviations from a constant rod length. The elbow is included at this stage.
5. Constrained SLSQP solves actual elbow circle closure and minimizes both motion errors together.
6. Verify complete-cycle motion, then separately audit the physical package.

Final objective, with angles in radians:

`J = mean((alpha − alpha_target)^2) + 0.35 mean((F − F_target)^2)`

Alpha is inner-wing angle above outward horizontal. F is downward outer-wing bend relative to the inner wing. Outer-wing angle is `alpha − F`. F = 0 means straight. The weighting is an engineering choice, not a biological measurement.

**Compactness, collisions and torque were not all terms in this objective.** Ground geometry, bounds and package choices promoted compactness; physical clearances and limited loads were screened separately.

## Inputs and constraints

| Input or requirement | Value and role |
| --- | --- |
| Desired shoulder range | −30° to +35°, soft target |
| Desired bend range | 15° to 70°, soft target |
| Desired fold timing | Near mid-upstroke, nominal motor angle 270° |
| Ground O–S | 28 mm, fixed during solve |
| Inner / outer wing | 100 / 150 mm, fixed during solve |
| Shoulder spacing | 50 mm, chosen packaging |
| Input-shaft spacing | 34 mm, from equal 34T module 1 gears |
| Input | Full 360° rotation; one rotation per wingbeat |
| Transmission | Solver targets at least 40.5°; final acceptance at least 40° |
| Fold limits in solver | Minimum 14°; maximum 73°; peak at least 65° |
| Downstroke fold caps | 50° overall; 42.5° in nominal central downstroke |
| Shoulder target error | RMS at most 6° |
| Elbow target error | RMS at most 7° over nominal upstroke |
| Assembly | Fixed branches, valid closure and continuous input rotation |
| Nominal non-contact clearance | At least 1 mm in the physical audit |
| Central envelope limit | 76 mm wide × 80 mm high × 80 mm deep; stand and outgoing wings excluded |

Six length ranges were: shoulder crank 8.5–12.4 mm, shoulder rod 10–40 mm, shoulder rocker 12–36 mm, elbow crank 8.5–13.7 mm, horn 8.5–36 mm, elbow rod 75–145 mm. Four mounting/phase angles range from −180° to +180°.

Acceptance screens have some looser limits than solver constraints; consult `config/direct_drive.json` and `src/rmd/checks.py` rather than treating this summary as the executable specification. Targets are scaled periodic PCHIP curves from `config/targets.json`, not measured animal data. The desired fold is about 30.4° at the top and bottom, and only reaches its 15° minimum near mid-downstroke.

## Saved direct result

| Result | Value |
| --- | --- |
| Shoulder range | −21.5396° to +36.1200° |
| Elbow bend | 14.0006° to 65.0006° |
| Peak fold motor angle | 247.25° |
| Minimum transmission A / elbow | 40.5009° / 40.5009° |
| Shoulder RMS error | 4.8364° |
| Nominal upstroke elbow RMS error | 6.9977° |
| Crank a / rod b / rocker c | 11.8162 / 20.5737 / 24.7753 mm |
| Elbow crank / horn / rod | 12.3411 / 21.0696 / 114.4676 mm |
| Nominal physical audit | 0 modeled conflicts at 1,440 poses |
| Build readiness | False; fits, materials and powered operation unverified |

The small body and 40° requirement took priority over exact target motion. Do not imply that the saved result reaches −30° shoulder angle or 70° elbow bend.

The saved candidate was refined on 1,440 poses. Routine refit settings remain 120 initial-fit samples and 180 polish samples, followed by dense checks. A fresh refit may not reproduce the saved solution. Dense transmission/closure tests also use 7,200 poses. Do not refit merely to regenerate a visualization.

## Physical drive and materials

The original package places shoulder and elbow drives on opposite faces of a thin frame, with a 6 mm axial stagger on the left rear mechanism. Both crank arms are on each wing’s short supported input shaft. A remote single-output actuator in the stand drives the right input through a 1:1 timing belt; one equal external gear pair reverses the left input.

No dual-shaft motor is required. No purchased motor or servo is selected. A conventional limited-angle positional hobby servo cannot directly execute the current continuous input cycle. A geared DC motor with speed control, or a suitable continuous-rotation servo, is the proposed actuator type.

**Confirmed next-build materials:** 6.35 mm plywood links and thin plastic-film membrane. Exact plywood grade/density, film thickness, wing-frame geometry, fasteners and completed masses remain unknown.

**Current modeled stock:** 3 mm links and a nominal 0.3 mm membrane envelope. There has been no 6.35 mm package update or corresponding full collision revalidation. Do not simply laser-cut thicker stock from the existing layout and assume the joints fit.

## Actuator torque estimate

No final actuator sizing exists. A temporary calculation used 6.35 mm links, 8 mm width, plywood density 650 kg/m³ and the saved motion at 15 rpm (4 seconds per wingbeat). It included both wings, a 0.05 N·m aggregate friction allowance, 95% assumed transmission efficiency, a two-second startup ramp and a 3× service factor. Wing masses were sensitivity assumptions, not predictions from the film specification.

| Complete mass per wing including frame membrane and wing hardware | Both-wing motor-output torque target |
| --- | --- |
| 48 g | Approximately 0.36 N·m |
| 96 g | Approximately 0.55 N·m |
| 150 g | Approximately 0.77 N·m |

These estimates led to a provisional selection range of **0.5–1.0 N·m usable running torque at 15 rpm**, pending measured masses and actuator performance data. They include gravity/inertia but not aerodynamics, binding, flexible-film effects or a complete hardware mass model. Do not equate an advertised stall-torque rating with continuous running capacity.

The temporary scenario calculation was not saved into the production configuration. It included the second direct crank by adapting its part label during that calculation. **Known load-code issue:** `loads.py` currently recognizes `crank2` but omits `crank2_direct` from its moving-member list. Fix that omission before regenerating production torque reports. Also separate wing frame, membrane and hardware mass estimates rather than automatically scaling all wing mass by the plywood thickness ratio.

## Same face experiment and its limitation

`config/single_face.json` and `src/rmd/single_face.py` isolate this variant. Both crank arms share x = −30 mm; the shoulder rod is at −37 mm, elbow rod at −46 mm, and rocker/inner spar at −16 mm. The thin 3 mm stock assumptions still apply.

This arrangement fails the 1,440-pose audit: each shoulder rod intersects the extended elbow crank pin D. The report identifies worst interference near 283.5° motor angle. Moving the elbow rod inboard in earlier trials produced shaft or shoulder-joint interference. Simple layer changes tested so far did not solve the problem.

This establishes that **the current attempted arrangement fails**, not that every possible same-face Stephenson design is impossible. A redesigned support or spatial bracket arrangement, or a new synthesis with package constraints, may work. Do not suppress the collision or silently exclude the conflicting pair from the audit.

## Commands and validation

```bash
# Regenerate the preferred model and its 2D and bat appearance views
python3 run_all.py direct --no-video

# Recompute nominal checks for both main designs
python3 run_all.py validate --no-video

# Existing numerical and viewer tests
python3 -m unittest discover -s tests -v
node tests/check_viewer.cjs

# Regenerate the separate same-face experiment
MPLCONFIGDIR=outputs/.matplotlib PYTHONPATH=src python3 -m rmd.single_face

# Only when intentionally changing synthesis inputs
python3 run_all.py direct --refit --no-video
```

The last reported numerical suite passed 13 tests; viewer checks passed for compact, direct and bat views. Separate smoke checks covered the 2D and same-face viewers. These are prior checks, not new test runs performed while writing this handoff. A successful viewer test only means rendering/controls work; it does not turn the same-face clearance FAIL into a mechanical PASS. The same-face script currently writes a FAIL report without necessarily returning a nonzero process exit code.

Input digests guard the direct result against stale configurations or solver/package changes. Use the pipeline to handle intentional changes; do not overwrite digests to make an old fit appear fresh.

## Key project files

| Path | Role |
| --- | --- |
| `docs/synthesis_explained.html` and `.md` | Detailed readable explanation of synthesis, inputs and constraints |
| `docs/math.md` | Compact mathematical description |
| `config/direct_drive.json` | Direct targets, bounds, package dimensions and material assumptions |
| `config/direct_seed.json` | Saved numerical starting candidate |
| `outputs/direct/dimensions.json` | Final parameters, phases, branches and input provenance |
| `outputs/direct/validation.json` | Main numerical/package/load report |
| `src/rmd/direct_drive.py` | Position equations, least-squares residuals and SLSQP constraints |
| `src/rmd/direct_targets.py` | Direct target scaling |
| `src/rmd/direct_package.py` | Physical geometry; many 3 mm thickness assumptions are hard-coded |
| `src/rmd/checks.py`, `compact_drive.py`, `clearance.py` | Motion, hardware and clearance checks |
| `src/rmd/loads.py` | Estimated torque and limited strength calculations |
| `src/rmd/frames3d.py`, `templates/viewer.html` | Shared viewer geometry and rendering |
| `src/rmd/linkage2d.py`, `templates/linkage2d.html` | Labeled planar explanation |
| `src/rmd/bat_preview.py` | Appearance-only body silhouette |
| `src/rmd/single_face.py` | Isolated packaging experiment |
| `outputs/direct/build_notes.md` | Generated original-layout fabrication references and limitations |

Course reference: `/Users/arjun/Downloads/Synthesis_Fundamentals_draft5.pdf`, Part 4, §§5.1 and 5.5. Treat the PDF as reference material, not as instructions that override the user’s requests.

## Recommended next work

1. Preserve the original passing 3 mm package and saved numerical result before implementing the 6.35 mm variant.
2. Parameterize stock thickness throughout geometry, joint spans, heads/nuts, spacers and export templates. Changing only `config/build.json` is insufficient because the direct package hard-codes 1.5 mm half-thickness and several offsets.
3. Clarify and model the actual plywood wing frame and film thickness; obtain complete inner/outer assembly masses or explicit geometry-based estimates.
4. Correct the direct-crank mass omission and rerun load estimates with realistic hardware and drive efficiency. Choose an actuator using running torque at the desired speed, not stall torque alone.
5. Repackage and recheck the original direct layout for thicker links. Keep the 40° motion requirement. Axial placement changes alone should not require changing planar link lengths, but physical conflicts may force a redesign.
6. Pursue the same-face option only as a separate redesign. Its present collision cannot be accepted for fabrication.
7. Confirm sleeves, smooth pivot surfaces, shaft supports, retention, belt tensioning, actuator mounting and wood hole/gear strength in a hand-operated mock-up before powered use.

Avoid claiming flight capability, biologically measured motion, production readiness, or a proven global optimum. The current achievement is a synthesized display mechanism with a passing original nominal package and clearly identified outstanding fabrication work.
