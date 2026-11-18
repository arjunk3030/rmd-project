# Spacer planning — two-wing mockup

**Do not cut spacers from this table yet.** The values are face-to-face gaps,
not verified spacer lengths. Bearing inner-ring seating, protrusion, washers,
retaining hardware and clearances are not specified. Some gaps may require
multiple spacers or a bearing carrier. Quantities below are the number of gaps
or joint stacks, not a confirmed bill of materials.

Inputs: wall **inside face gap 20.00 mm**, wall thickness 4.00 mm,
link thickness 3.70 mm. The wall centers are at ±12.00 mm.

| Location | Gap or stack quantity, both wings | Nominal face gap (mm) | Design needed |
|---|---:|---:|---|
| A: crank to shoulder coupler | 2 | 16.30 | Inner-race spacer stack per pivot |
| B: shoulder coupler to triangle | 2 | 2.30 | Inner-race spacer stack per pivot |
| D: crank to elbow coupler | 2 | 16.30 | Inner-race spacer stack per pivot |
| Q: elbow coupler to outer L | 2 | 2.30 | Inner-race spacer stack per pivot |
| E: triangle to outer L | 2 | 64.30 | Long shaft requires supported carrier and separate bearing spacers; not a single specified sleeve |
| S: triangle to adjacent wall | 2 | 18.15 | Locate shoulder assembly; race arrangement and support not yet designed |
| O: crank face to adjacent wall | 4 | 4.15 | Establish bearing and shaft stops; the crank hub projects outward |
| Three gears: gear face to inside wall | 6 | 5.00 | Position gears; gear hubs, bearing-race locations and stops not yet designed |
| Between the two wall inside faces | 1 assembly | 20.00 | Structural standoffs, quantity/positions not yet designed; do not infer a single loose spacer per shaft |

At O, the 4.15 mm gap is measured from the printed crank face to
the wall. The 10 mm-long crank hub projects away from that wall. A collar, bearing
or hub can occupy a listed gap. The E faces are 64.30 mm apart with current link
planes and thickness; this span is a structural concern, not a recommendation to
make a 64.3 mm unsupported tube.

## Conditional CAD placeholders — not manufacturing dimensions

The following numbers answer “what length would bridge the space?” **only if**
each 3.00 mm-wide bearing is centered in its link or wall, the
spacer contacts the inner race directly, exactly one spacer is used per listed
gap, and no washer or shoulder occupies that gap. The supplied STL bearing
seats and race contact geometry have not been confirmed. Wall-bearing-to-gear
and wall-bearing-to-crank entries additionally require suitable shaft-fixed
hub contact surfaces. These are starting dimensions for CAD, not a purchase or
print list; verify contact faces and clearance first.

| Tentative spacer location | Hypothetical quantity, both wings | Nominal axial span (mm) |
|---|---:|---:|
| A: shoulder crank bearing to coupler bearing | 2 | 17.00 |
| B: shoulder coupler bearing to triangle bearing | 2 | 3.00 |
| D: elbow crank bearing to coupler bearing | 2 | 17.00 |
| Q: elbow coupler bearing to L bearing | 2 | 3.00 |
| S: triangle bearing to adjacent wall bearing | 2 | 19.00 |
| O: support bearing to crank face, both sides | 4 | 4.65 |
| Gear face to wall bearing, both sides, three gears | up to 6 | 5.50 |

For E, the bearing-center-plane separation is 68.00 mm.
Do **not** CAD a full-length sleeve as the solution: the shaft needs an actual
supported carrier, whose bearings, axial positions and spacers have not been designed.
Nominal 6 mm shaft bores are only starting geometry; select the actual shaft fit.
Spacers must contact only the bearing inner race, not rub its outer race, seal or
rotating link. Their outside diameters depend on the bearing maker's dimensions.

## Changing the wall spacing

Edit `wall_inner_gap_mm` in `config/presentation/mockup.json`, then run
`python3 run_all.py working-mockup`. The visualization and this schedule will
regenerate using that inside-face gap. The wing-link planes remain fixed, so A,
B, D, E and Q gaps do not change; S, O, gear-to-wall and wall-to-wall gaps do.
This model does not automatically redesign shaft lengths, motor supports,
washers or fasteners when the gap changes. Recheck them and full-cycle clearance.

## Basic axial checks

- No overlap in these simple *axial face-gap* calculations. This does not check moving parts, shafts, collars or fasteners.

Checks use nominal face positions only, not actual STL geometry, bearing fits,
pin grooves, motor mounts, gear hubs, tolerance, deflection or collision checks.
The current uploaded triangle's pivot positions do not match the design.
