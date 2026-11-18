# Two-wing split-face mockup concept

The 1.25-scale saved pivot motion is unchanged; the animated outer arm is 150 mm
to match L Linkage (5).stl, not the 187.5 mm design target. The supplied triangle
STL has different pivot spacings and is NOT represented: its three distances are
approximately 34.36, 116.91 and 133.32 mm, versus the 1.25× triangle's 30.97,
116.59 and 125.00 mm. Both wings have separate O shafts;
their centers are 56 mm apart to allow the wing gears to mesh directly.
Two 20 mm OD × 10 mm clamp hubs are shown per wing. Axial planes in mm:
shoulder coupler −40, triangle −34, shoulder crank −20, supports ±9.5,
elbow crank +20, outer L +34, elbow coupler +40. All pivot shafts are shown as
6 mm diameter. E has a nominal 20 mm OD × 8 mm collar on its triangle side; the other
end and the A, B, D, Q and S joints have schematic 1 mm retaining rings, not
selected parts. The input crank hubs retain the O shaft in the illustration.
Approximate drawing lengths per wing: O 73.7, A 35.7, B 21.7, S 59.2,
D 35.7, E 88.7, Q 21.7 mm. These are visualization envelopes, not cut lengths.
Each link is 3.7 mm thick. The A and D joint part faces are 16.3 mm apart,
and B and Q faces are 2.3 mm apart; these joints need actual inner-race spacers.
The E parts are 64.3 mm apart, so the long shaft needs a supported carrier or
revised packaging. The 10 mm long crank hubs end only 0.3 mm from the adjacent
triangle/L planes; tolerances, clamp ears and hardware make that a serious
assembly concern. Sleeves, washers, collars and support of these stacks have
not been designed in CAD. The simplified shaft/bar check is in
shaft_bar_screen.json and does not include those features.

This is NOT clearance-validated or fabrication-ready. In particular, the chosen
20 mm hubs, ears, clamp screws, enlarged links, supports, collars, shafts and
motor have not had a full moving-solid collision, retention or load check.
The L is drawn from the supplied L Linkage (5).stl face outline; its E–Q pivot
spacing already matches the 1.25× design and E–T is 150 mm in the file. No
stretching is applied to the L outline or bearing holes.
The clamp is a simplified representation of the supplied coupler STL, not its
exact mesh. The STL appears to use meters while the L file uses millimeters.
An illustrative 16T motor pinion drives a 56T wing gear that meshes directly
with the other 56T wing gear. At module 1, the 56 mm O–O pitch layout reverses
the wing shafts; motor to wing ratio is 56:16 = 3.5:1. Teeth are illustrative profiles.
The nominal 29 mm gear tip radius leaves 3 mm from the 6 mm shoulder shaft,
because O–S is 35 mm. Actual teeth, tolerances and
shaft hardware need a full clearance check. Gear backlash, printing accuracy,
gears' attachment, idler loading, motor mount, motor
shaft extension, support holes and all moving-solid clearances are unverified.
The motor is a 24 × 20 × 20 mm placeholder, not a selected gearmotor. Its body
starts at x=45 mm on a long motor-shaft extension; the required standoff bracket,
shaft support and coupling are not designed. Two
20 mm OD × 8 mm collars are at the E pivots. The
previous placement of the larger elbow collar on the opposite end intersected
the elbow coupler and was not retained. Full assembly remains unverified.
Shaft collars must be selected with a 6 mm bore and dimensioned with actual
hardware and retention. The 88.7 mm E shaft is an unsupported-length concern.

Gear width is 10.00 mm and the wall inside gap is 20.00 mm. With gears centered, nominal gear-face to wall-face gap is 5.00 mm per side. This is not a spacer length or proof that gear hubs, shaft stops and bearing races fit.
