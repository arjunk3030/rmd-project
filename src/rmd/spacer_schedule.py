"""Generate a gap and quantity schedule from the mockup's displayed layers."""


def write_schedule(cfg, planes, path):
    t = float(cfg['plate_thickness_mm'])
    wall_gap = float(cfg['wall_inner_gap_mm'])
    wall_thickness = 4.0
    wall_outer = wall_gap / 2 + wall_thickness
    crank_inner = abs(planes['crank1']) - t / 2
    face_gap = lambda a, b: abs(planes[a] - planes[b]) - t
    a = face_gap('crank1', 'coupler1')
    b = face_gap('rocker1', 'coupler1')
    d = face_gap('crank2_direct', 'rod2_direct')
    q = face_gap('elbow_horn', 'rod2_direct')
    e = face_gap('inner_spar', 'outer_spar')
    shoulder = abs(planes['rocker1']) - t / 2 - wall_outer
    crank_support = crank_inner - wall_outer
    gear_support = (wall_gap - cfg['gear_stack']['gear_width_mm']) / 2
    bearing_width = float(cfg['bearing_width_mm'])
    wall_center = (wall_gap + wall_thickness) / 2
    race_a = abs(planes['crank1'] - planes['coupler1']) - bearing_width
    race_b = abs(planes['rocker1'] - planes['coupler1']) - bearing_width
    race_d = abs(planes['crank2_direct'] - planes['rod2_direct']) - bearing_width
    race_q = abs(planes['elbow_horn'] - planes['rod2_direct']) - bearing_width
    race_s = abs(planes['rocker1'] + wall_center) - bearing_width
    wall_bearing_to_crank = abs(planes['crank1']) - t/2 - wall_center - bearing_width/2
    wall_bearing_to_gear = wall_center - bearing_width/2 - cfg['gear_stack']['gear_width_mm']/2
    problems = []
    for name, value in [('A',a),('B',b),('D',d),('Q',q),('E',e),
                        ('shoulder to wall',shoulder),('crank to wall',crank_support),('gear to wall',gear_support)]:
        if value <= 0:
            problems.append(f'- **{name}: {value:.2f} mm — overlapping or zero clearance.**')
    warning = '\n'.join(problems) if problems else '- No overlap in these simple *axial face-gap* calculations. This does not check moving parts, shafts, collars or fasteners.'
    path.write_text(f'''# Spacer planning — two-wing mockup

**Do not cut spacers from this table yet.** The values are face-to-face gaps,
not verified spacer lengths. Bearing inner-ring seating, protrusion, washers,
retaining hardware and clearances are not specified. Some gaps may require
multiple spacers or a bearing carrier. Quantities below are the number of gaps
or joint stacks, not a confirmed bill of materials.

Inputs: wall **inside face gap {wall_gap:.2f} mm**, wall thickness {wall_thickness:.2f} mm,
link thickness {t:.2f} mm. The wall centers are at ±{(wall_gap+wall_thickness)/2:.2f} mm.

| Location | Gap or stack quantity, both wings | Nominal face gap (mm) | Design needed |
|---|---:|---:|---|
| A: crank to shoulder coupler | 2 | {a:.2f} | Inner-race spacer stack per pivot |
| B: shoulder coupler to triangle | 2 | {b:.2f} | Inner-race spacer stack per pivot |
| D: crank to elbow coupler | 2 | {d:.2f} | Inner-race spacer stack per pivot |
| Q: elbow coupler to outer L | 2 | {q:.2f} | Inner-race spacer stack per pivot |
| E: triangle to outer L | 2 | {e:.2f} | Long shaft requires supported carrier and separate bearing spacers; not a single specified sleeve |
| S: triangle to adjacent wall | 2 | {shoulder:.2f} | Locate shoulder assembly; race arrangement and support not yet designed |
| O: crank face to adjacent wall | 4 | {crank_support:.2f} | Establish bearing and shaft stops; the crank hub projects outward |
| Three gears: gear face to inside wall | 6 | {gear_support:.2f} | Position gears; gear hubs, bearing-race locations and stops not yet designed |
| Between the two wall inside faces | 1 assembly | {wall_gap:.2f} | Structural standoffs, quantity/positions not yet designed; do not infer a single loose spacer per shaft |

At O, the {crank_support:.2f} mm gap is measured from the printed crank face to
the wall. The 10 mm-long crank hub projects away from that wall. A collar, bearing
or hub can occupy a listed gap. The E faces are {e:.2f} mm apart with current link
planes and thickness; this span is a structural concern, not a recommendation to
make a 64.3 mm unsupported tube.

## Conditional CAD placeholders — not manufacturing dimensions

The following numbers answer “what length would bridge the space?” **only if**
each {bearing_width:.2f} mm-wide bearing is centered in its link or wall, the
spacer contacts the inner race directly, exactly one spacer is used per listed
gap, and no washer or shoulder occupies that gap. The supplied STL bearing
seats and race contact geometry have not been confirmed. Wall-bearing-to-gear
and wall-bearing-to-crank entries additionally require suitable shaft-fixed
hub contact surfaces. These are starting dimensions for CAD, not a purchase or
print list; verify contact faces and clearance first.

| Tentative spacer location | Hypothetical quantity, both wings | Nominal axial span (mm) |
|---|---:|---:|
| A: shoulder crank bearing to coupler bearing | 2 | {race_a:.2f} |
| B: shoulder coupler bearing to triangle bearing | 2 | {race_b:.2f} |
| D: elbow crank bearing to coupler bearing | 2 | {race_d:.2f} |
| Q: elbow coupler bearing to L bearing | 2 | {race_q:.2f} |
| S: triangle bearing to adjacent wall bearing | 2 | {race_s:.2f} |
| O: support bearing to crank face, both sides | 4 | {wall_bearing_to_crank:.2f} |
| Gear face to wall bearing, both sides, three gears | up to 6 | {wall_bearing_to_gear:.2f} |

For E, the bearing-center-plane separation is {abs(planes['inner_spar']-planes['outer_spar']):.2f} mm.
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

{warning}

Checks use nominal face positions only, not actual STL geometry, bearing fits,
pin grooves, motor mounts, gear hubs, tolerance, deflection or collision checks.
The current uploaded triangle's pivot positions do not match the design.
''')
