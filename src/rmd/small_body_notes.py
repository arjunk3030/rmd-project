"""Documentation specific to the small plywood package, avoiding legacy motor claims."""
def write_notes(out,r,cfg):
    k=r['kinematics'];cover=cfg['body_cover'];xy=cover['outline_yz_mm']
    width=max(p[0] for p in xy)-min(p[0] for p in xy);height=max(p[1] for p in xy)-min(p[1] for p in xy)
    text=f'''# Small-body plywood bat — numerical prototype

Nominal checks: **{r['status']}**. Hardware and loaded operation are unverified.

## Small body is a design requirement

The shoulder pivots are {cfg['shoulder_spacing_mm']} mm apart; O–S ground is
{cfg['ground_mm']} mm. The front bat face is {width:g} x {height:g} x 3 mm.
Inner/outer wing lengths are 100/150 mm. Body bearings are small 3 mm-shaft plain
bushings, not the former 16 mm ball bearings and 24 mm housings. Shaft hubs are
8 mm OD trial envelopes, the elbow sleeve carrier is 9 mm OD.

One single-output continuous actuator is placed in the stationary pedestal.
A 20T/20T, 2 mm pitch belt drives right O; a 34T gear pair reverses left O.
Both cranks are fixed to each short O shaft, on opposite sides of the thin frame.
A moves the shoulder; B's rod directly moves the outer-wing horn. The gears no
longer carry the elbow crank pins: cut separate crank2_direct arms.

The body mechanism is compact because the motor has moved out of it. The stand,
belt and actuator reservation remain visible and are part of the model. This is
a stationary display, not a self-contained flying robot. No actual servo model
is selected; a standard limited-angle hobby servo cannot directly run this
continuous 360-degree input. Select torque, spline, supply and driver before
finishing the pedestal. Actuator-control firmware is not supplied.

## Targets and synthesis

User-proposed targets: shoulder +35/-30 degrees, fold 15..70 degrees, maximum
fold at mid-upstroke. These are stylistic targets, not measured animal motion.
They replace the earlier straight-downstroke condition. Joint bounded numerical
synthesis solves both loops with 28 mm ground; full-cycle constraints retain
40-degree minimum transmission, prioritized over exact shoulder sweep. Output dimensions are in dimensions.json;
parameter angles are radians, motion.csv is degrees. All stock/clearance and
material assumptions remain editable in config/direct_drive.json.

Actual shoulder: {k.get('min_alpha_deg',0):.2f}..{k.get('max_alpha_deg',0):.2f} degrees.
Actual fold: {k['min_F_deg']:.2f}..{k['max_F_deg']:.2f} degrees.
Minimum transmission A/elbow: {k['mu1_min_deg']:.2f}/{k['mu2_min_deg']:.2f} degrees.
Modeled conflicts: {r['clearance']['conflict_count']} across {r['clearance']['samples']} poses.
Running-torque estimate: {r['loads']['required_running_torque_target_Nm']:.3f} Nm;
this uses guessed masses, stiffness and friction, not verified actuator capacity.

## Build references

Use 3 mm plywood links, smooth 3 mm metal pivot pins, washers/spacers and small
metal shaft hubs. Pin-center dimensions and trial 3.2 mm holes are in the 1:1
SVGs. 8 mm link width leaves only a small ligament around holes: check grain,
ply quality, hole wear and tear-out. Do not tighten a retaining nut against a
moving wood face. Use a sleeve/shoulder surface and retain it with running freedom.

The 3 mm gear outlines are nominal geometry; tooth accuracy, root fillets,
strength and hub attachment remain unverified. Purchased gears may be more
practical than fine laser-cut plywood teeth. Sleeve OD trial seats are 6.1 mm.
All shaft/hub/bushing fits must be measured before final fabrication.

Fabric panels are separate at the elbow with a 10 mm relief; root relief is
20 mm. Rib roots start 20 mm out along the inner wing to clear the frame. Avoid
a taut fabric bridge across the elbow. Keep covers clear throughout the cycle.
The bat_body_1to1.svg face is removable. Its geometry is checked, but its mounting
brackets/fasteners and belt tensioner are not finished production details.

Assemble at the zero pose in layout.json, clamp the crank phases, and hand-turn
a full cycle before powered testing. Keep shoulders and elbows free. Load checks
cover only an ideal rod/shaft case; they do not qualify wood tear-out, gear teeth,
fasteners, belt tension, bearing wear or fabric flexibility.
'''
    (out/'build_notes.md').write_text(text)
