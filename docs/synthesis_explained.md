# How the bat wing mechanism was synthesized

Current direct Stephenson six-bar design • 19 October 2026

We sized the shoulder and elbow mechanism together using numerical optimization of position equations. The method follows Part 4 of Synthesis Fundamentals draft 5, with the six-bar extension described in section 5.5. The final direct design was not obtained from two independent Freudenstein solutions.

This document separates chosen inputs, adjustable dimensions, optimization objectives, constraints and subsequent physical checks. “Fixed” means held constant during this solve. Most chosen values remain editable; they are not measured biological facts.

## 1 What moves and what the angles mean

For one wing, the shoulder four-bar moves the inner wing. An additional two-link dyad—the elbow rod and the outer wing with its rigid horn—controls the elbow bend. Both crank arms are rigidly fixed to one input shaft. The two arms and shaft therefore count as one link, even when manufactured as separate pieces.

The six links are the fixed frame, common crank assembly, shoulder connecting rod, shoulder rocker with inner wing, elbow connecting rod, and outer wing with horn. The two three-joint links are O–A–D and S–B–E. They do not share a pivot directly, giving the Stephenson topology. Only O and S are fixed to the frame; the triangles representing those rigid assemblies move.

| Quantity | Definition | Example |
| --- | --- | --- |
| Motor angle θ | Input-shaft rotation through one wingbeat | 0° to 360° per cycle |
| Shoulder angle α | Inner-wing angle relative to outward horizontal | Positive is up; negative is down |
| Elbow bend F | Downward fold of the outer wing relative to the inner wing | 0° is straight; 65° is strongly folded |
| Outer-wing angle | α − F relative to outward horizontal | α = 35°, F = 65° gives −30° |

Left and right wings use mirrored outward coordinates. One actuator synchronizes both wing mechanisms through the transmission. There is no independently commanded elbow input.

## 2 Did we synthesize the four bar first

**In the current direct solve, no: we did not finish and freeze a shoulder four-bar and then independently synthesize the elbow. We optimized the complete six-bar together.**

However, position analysis must proceed in order. For any trial set of dimensions, we first calculate the shoulder linkage, because that tells us where the elbow E is. We then calculate the elbow linkage using that moving elbow position. The optimizer scores both motions and can change either section before trying again.

Calculation order within every trial:

Motor angle → shoulder position → elbow location → outer-wing position → errors and constraints

That order is not two independent synthesis problems. It is how the coupled mechanism is evaluated. When a shoulder dimension changes, the elbow location changes, and the outer-wing motion is recalculated immediately.

The first fitting stage already includes the elbow: it places the horn at the desired bend and measures whether a constant-length rod can reach it. The refinement stage then uses the actual rod-constrained elbow motion instead. **We never discard the elbow while sizing the current mechanism.**

Earlier project work included a geared four-bar design and numerical starting guesses. The current direct solver starts from a saved numerical candidate and tries refinements and alternative starts. That history is not evidence that the final six-bar is an exact Freudenstein solution.

## 3 What was given to the design

### Desired motion

These are aesthetic targets estimated for the project, not motion measured from an animal. We fit the entire cycle, not only its extreme angles. The desired downstroke occupies the first half of the nominal cycle; the upstroke occupies the second half.

| Input | Desired value | Treatment |
| --- | --- | --- |
| Shoulder range | −30° to +35° | Soft motion target |
| Elbow bend range | 15° to 70° | Soft motion target |
| Maximum fold timing | Near 270° motor angle, mid-upstroke | Shape of target curve; timing also screened |
| Downstroke appearance | More extended than on the upstroke | Target curve and fold caps |
| Input motion | Continuous full revolution | Required assembly and drive behavior |
| Left and right motion | Mirrored and synchronized | Imposed by the chosen architecture |

The actual target samples, after scaling the shared timing curve, are:

| Motor angle | Shoulder target α | Elbow target F |
| --- | --- | --- |
| 0° | 35.00° | 30.40° |
| 45° | 25.51° | 18.85° |
| 90° | 2.50° | 15.00° |
| 135° | −20.51° | 18.85° |
| 180° | −30.00° | 30.40° |
| 225° | −20.51° | 57.35° |
| 270° | 2.50° | 70.00° |
| 315° | 25.51° | 57.35° |
| 360° | 35.00° | 30.40° |

The code interpolates these with a periodic, shape-preserving PCHIP curve. Notice that “15° minimum bend” does not mean 15° for the whole downstroke. Likewise, the desired fold at the top and bottom is about 30°.

### Dimensions held fixed during this solve

| Input | Value | Why it was chosen |
| --- | --- | --- |
| Shoulder-to-input ground distance O–S | 28 mm | Compact shoulder mechanism |
| Inner wing length | 100 mm | Selected proportions |
| Outer wing length | 150 mm | Selected proportions; does not enter the elbow rod closure |
| Shoulder spacing across body | 50 mm | Body packaging |
| Input-shaft spacing across body | 34 mm | Equal 34-tooth module 1 gear pair |
| One wing’s local ground pivots | S = (0, 0); O = (−8, −26.833) mm | Derived from the above layout |
| Drive architecture | One actuator, two common crank arms per wing | Mechanically couples shoulder and elbow |

The original direct package also uses a remote actuator in the stand, equal 20-tooth belt pulleys and a reversing gear pair. These are packaging decisions, not variables in the ten-variable motion optimization. The display cycle is 4 seconds, or 15 rpm; timing changes load estimates but not the angle-versus-crank geometry.

### Adjustable design variables

| Variable | Meaning | Search range |
| --- | --- | --- |
| a | Shoulder crank length | 8.5–12.4 mm |
| b | Shoulder connecting rod length | 10–40 mm |
| c | Shoulder rocker length | 12–36 mm |
| κ | Rocker-to-inner-wing mounting angle | −180° to +180° |
| pA | Shoulder crank mounting phase | −180° to +180° |
| aD | Elbow-drive crank radius | 8.5–13.7 mm |
| pD | Elbow crank mounting phase | −180° to +180° |
| h | Elbow horn length | 8.5–36 mm |
| η | Horn-to-outer-wing mounting angle | −180° to +180° |
| L | Elbow connecting rod length | 75–145 mm |

These ranges were chosen search limits. Both crank phases are fixed mounting angles after construction, not separately controlled motions.

## 4 The mathematical synthesis steps

### Step 1 Build a candidate

Choose a trial vector x = [a, b, c, κ, pA, aD, pD, h, η, L] within its bounds. Let u(γ) = (cos γ, sin γ). All calculation angles use radians, though results are displayed in degrees.

### Step 2 Solve the shoulder at each motor angle

The shoulder crank pin is A = O + a u(θ + pA). Find B by intersecting two circles:

|B − S| = c and |B − A| = b.

Then α = atan2(B − S) − κ, and the elbow position is E = S + 100 u(α). Here atan2 of a vector means its direction angle. The code handles angle wrapping and keeps a selected circle-intersection branch.

### Step 3 Include the elbow in the initial least squares fit

The second crank pin is D = O + aD u(θ + pD). Using the desired elbow bend F*, form the desired horn point:

Q* = E + h u(α − F* + η).

The rod-length error is eL = |Q* − D| − L. If this is zero at every pose, one rigid rod can produce those desired horn poses for that shoulder motion.

The initial fit minimizes squared residuals including 35(α − α*) and eL, plus penalties for poor transmission, failed shoulder assembly and unsuitable shoulder link proportions. The factor 35 is a chosen weighting that balances angular and length errors. It is not a material property. Bounded least squares supplies candidates; both shoulder and elbow variables participate.

### Step 4 Calculate the actual elbow motion

The final stage does not assume that the target is reached. It finds Q by intersecting circles:

|Q − E| = h and |Q − D| = L.

The actual fold is F = α + η − atan2(Q − E). This expresses how a rod of fixed length constrains the outer wing. The outer-wing tip is T = E + 150 u(α − F).

### Step 5 Minimize motion error with constraints

The final objective is:

J = mean[(α − α*)²] + 0.35 mean[(F − F*)²].

The first term measures shoulder error over the cycle. The second measures elbow error over the cycle. The weight 0.35 is an engineering choice. Separate error limits prevent an excessive sacrifice of elbow accuracy.

SLSQP adjusts the complete design vector while satisfying the constraints below. This is joint constrained numerical synthesis. It is not proof of a unique or globally optimal design. Multiple starts help explore possible solutions but do not prove optimality.

### Step 6 Check the complete result

Recompute the mechanism over the full cycle, check closure and motion, and then build and audit the physical geometry. The saved final result was refined on 1,440 poses; the regular refit settings currently use 120 initial-fit samples and 180 refinement samples, followed by dense verification. A routine refit is therefore not guaranteed to reproduce the saved dimensions exactly. Transmission and closure have also been checked on 7,200 poses.

## 5 Constraints and acceptance checks

Solver constraints and the later acceptance screen are related but not identical. Margins in the solver help protect the final minimum when the cycle is sampled more densely.

| Requirement | Solver condition | Subsequent acceptance |
| --- | --- | --- |
| Transmission angle | At least 40.5° in each loop | At least 40° |
| Circle assembly | Positive intersection-height margin in both loops | Valid full-cycle closure on fixed branches |
| Shoulder drive | Crank shortest; strict Grashof margin | Full input rotation and Grashof check |
| Minimum elbow bend | At least 14° | At least 12° |
| Maximum bend | No more than 73°; peak at least 65° | Peak between 65° and 75° |
| Downstroke bend | No more than 50° | No more than 52° |
| Central downstroke bend | No more than 42.5° for θ = 45°–135° | No more than 45° |
| Shoulder extrema | Reaches at least +30° and −18.5° or lower | Maximum 30°–40°; minimum −35° to −18° |
| Shoulder target error | RMS no more than 6° | Same error limit |
| Elbow target error | RMS no more than 7° over nominal upstroke | Same error limit |
| Peak-fold timing | Encouraged by the target curve | Peak on upstroke and near θ = 240°–300° |

The solver constrains bend over both the nominal first half-cycle and poses identified as moving downward. Ordinary independent-four-bar Grashof classification applies to the shoulder loop, not separately to the elbow loop, whose elbow pivot moves.

The two transmission checks are local coupler-to-output angles. They do not by themselves prove adequate motor torque or safe loads throughout the complete six-bar.

### Physical checks after the motion optimization

The ten-variable objective did not minimize collisions, body volume or motor torque. We chose the package, adjusted axial layers, and screened the resulting geometry separately.

| Package assumption or check | Value or scope |
| --- | --- |
| Nominal clearance requirement | 1 mm between non-contacting modeled envelopes |
| Body envelope limit | 76 mm wide × 80 mm high × 80 mm deep |
| Envelope scope | Central mechanism; excludes outgoing wing links and remote stand |
| Link stock | Assumed 3 mm plywood |
| Shafts | Assumed 3 mm metal shafts |
| Fabric envelope | Assumed 0.3 mm thickness |
| Wing relief | 20 mm at root and 10 mm at hinge |
| Original layer placement | Shoulder and elbow drives on opposite frame faces; 6 mm left rear stagger |
| Additional checks | Gear envelopes, mounting space and limited rod/shaft load estimates |

Mass, friction, stiffness, bushing fits, fastener retention, wood tear-out, gear strength and fabric behavior remain assumptions or require physical testing. The actuator is reserved geometrically but not selected or torque-qualified. The former small body cover remains in the original audit configuration but is hidden in the mechanical viewer; the larger cartoon costume is only an appearance study.

## 6 What the design achieved

| Quantity | Saved direct result |
| --- | --- |
| Shoulder range | Approximately −21.54° to +36.12° |
| Elbow bend range | Approximately 14.00° to 65.00° |
| Peak fold | Approximately 247.25° motor angle |
| Minimum transmission angles | Approximately 40.50° in both loops |
| Shoulder crank a | 11.816 mm |
| Shoulder rod b | 20.574 mm |
| Shoulder rocker c | 24.775 mm |
| Elbow crank aD | 12.341 mm |
| Elbow horn h | 21.070 mm |
| Elbow rod L | 114.468 mm |
| Original package clearance | No modeled conflicts at 1,440 poses |

The requested 65° shoulder sweep became about 58°, and the requested 70° maximum bend became 65°. These were deliberate compromises to preserve transmission quality and the chosen compact package. The quoted machining precision is not a manufacturing tolerance; final fits and tolerances must be specified separately.

### The same face experiment is different

The same-face version reuses the exact motion synthesis. It moves the parts into different depth layers and combines the crank arms into a common plane. It was not a new optimization of the six-bar lengths.

Its clearance check fails: the shoulder connecting rod intersects the extended elbow crank pin on each wing. The animation is a packaging comparison, not a buildable alternative as shown. The original direct layout remains the nominally passing version. A revised package or new synthesis is needed to make a practical same-face arrangement.

## 7 Where to inspect or change the design

| File | Purpose |
| --- | --- |
| config/direct_drive.json | Chosen dimensions, targets, search bounds and limits |
| config/targets.json | Shared target timing samples |
| src/rmd/direct_targets.py | Scales shared samples to the direct motion targets |
| src/rmd/direct_drive.py | Position equations, residuals and constrained optimization |
| config/direct_seed.json | Saved numerical starting candidate |
| outputs/direct/dimensions.json | Synthesized parameters and input provenance |
| outputs/direct/validation.json | Recomputed motion, package and load checks |
| outputs/direct_2d.html | Labeled one-wing diagram and rigid-link triangles |
| outputs/direct_3d.html | Original mechanical package |
| outputs/single_face_3d.html | Same-face experiment with known interference |

Course reference: Synthesis Fundamentals draft 5, Part 4 (especially sections 4.2–4.6), section 5.5 for adding a dyad and sizing the resulting mechanism, and section 5.1 for screening. Our SLSQP refinement is an implementation addition to the general optimization approach illustrated in the sheet.

A concise report description is: “We chose a Stephenson six-bar architecture by adding an elbow dyad to a shoulder four-bar. We jointly synthesized its lengths and mounting angles through bounded least squares and constrained optimization, followed by full-cycle motion and physical-envelope screening.”
