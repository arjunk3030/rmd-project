## 2. Candidates and synthesis

We considered a **geared pair of four-bar loops** and a **direct Stephenson six-bar**, each mirrored to drive both wings with one actuator. The first candidate targeted approximately ±25° shoulder motion and up to 50° elbow bend. The second used the revised targets in Part 1. Because the targets evolved, we compare their architecture, size and achieved motion rather than claiming an identical-target optimization comparison.

### Candidate 1 — Geared four-bar loops

This candidate uses a shoulder crank–rocker and a second four-bar that folds the outer wing. The inner wing acts as the second loop's moving reference link, while gearing supplies its crank rotation about the shoulder. We fixed the shoulder ground length at **50 mm** and the inner/outer wing lengths at **110/140 mm**.

We used **Freudenstein synthesis to obtain initial dimensions**, then optimization to improve the whole cycle. Three angle pairs make Freudenstein useful here: they give three linear equations for three length-ratio constants. The shoulder pairs were **(0°, +25°), (90°, 0°), and (180°, −25°)**, expressed as motor angle and desired wing angle. The equation is **K₁ cos(ψ) − K₂ cos(φ) + K₃ = cos(φ − ψ)**, where **K₁ = d/a**, **K₂ = d/c**, and **K₃ = (a² − b² + c² + d²)/(2ac)**. Once the constants are solved, the fixed ground length sets the scale.

The important free choice was the **rocker's mounting angle relative to the wing**. A wing angle is not automatically the rocker angle required by Freudenstein, so we searched mounting offsets and assembly branches rather than assuming they were identical. We retained a shoulder seed that reached the three prescribed pairs on one branch and could rotate through the cycle.

The elbow could not be synthesized as if its base were stationary. We first simulated the shoulder seed to obtain its actual angle α, then expressed the elbow input and output in the inner-wing frame: **u₂ = −θ + δ − α** and **v₂ = η − F**, where δ is drive phase, η is horn offset, and F is elbow bend. Using motor/fold targets **(0°, 14°), (180°, 14°), and (270°, 50°)**, we searched δ, η and branch choices and solved a second Freudenstein system. Subtracting the actual α is what couples this calculation to the shoulder result.

Matching three positions does not ensure acceptable motion between them. We therefore refined both loops together using bounded least squares and constrained SLSQP, reducing shoulder and fold errors while enforcing assembly, downstroke fold limits and transmission requirements. The changes from analytical seed to final dimensions show why the full-cycle refinement mattered:

| Link length | Freudenstein seed (mm) | Final (mm) |
| --- | ---: | ---: |
| Shoulder crank / rod / rocker | 15.11 / 48.43 / 36.03 | **16.41 / 38.65 / 40.39** |
| Elbow crank / rod / horn | 15.60 / 95.20 / 37.71 | **13.92 / 96.91 / 34.37** |

The refined mechanism achieved **50.47° peak fold** and minimum transmission angles of **50.24° and 44.10°**. Its saved package had no modeled collisions, but the complete two-wing drive required **six gears**.

### Candidate 2 — Direct Stephenson six-bar

To simplify the transmission and shrink the body, we placed both crank arms on each wing's **common input shaft**. The shoulder four-bar plus the elbow rod and outer wing forms a **Stephenson six-bar**, following the four-bar-plus-dyad architecture in §5.5. We fixed the ground distance at **28 mm** and the wing segments at **100/150 mm**.

We used **joint optimization following Part 4**, rather than two independent Freudenstein solves. In this arrangement, the elbow rod connects the common input crank to a horn on the moving outer wing. Changing a shoulder dimension changes the elbow's position and therefore changes the folding motion. Freezing the shoulder first would unnecessarily restrict the elbow solutions, so the optimizer adjusted **six lengths and four mounting/phase angles together**.

The initial fit asked a practical geometric question: **could one constant-length rod reach the desired elbow poses throughout the cycle?** For each candidate, the shoulder motion locates the elbow E. The desired horn point is **Qtarget = E + h u(α − Ftarget + η)**, where **u(γ) = (cos γ, sin γ)**. If D is the elbow crank pin and L is rod length, the residual **|Qtarget − D| − L** measures the mismatch. Bounded least squares reduces this mismatch alongside shoulder-angle error and mechanical penalties. The elbow is included from the beginning; calculating the shoulder first is only necessary to locate E.

The final refinement replaces the desired horn position with the **actual position permitted by the rigid rod**, found from **|Q − E| = h** and **|Q − D| = L**. We then minimize **J = mean[(α − αtarget)²] + 0.35 mean[(F − Ftarget)²]**, using radians. The weight 0.35 sets the relative preference for elbow tracking; it is a design choice. The targets are smooth curves through the angle pairs in Part 1, not positions that must be reached exactly.

The main tradeoff was between matching the estimated motion and preserving force transmission. We constrained both transmission angles to **at least 40.5° during refinement**, providing margin above the **40° acceptance limit**. We also required full-cycle assembly, limited fold during the downstroke, and imposed RMS error limits of **6° for the shoulder** and **7° for elbow motion during the nominal upstroke**. This allowed some departure from the desired extrema instead of accepting a near-toggle mechanism merely because its animation matched the targets better.

| Synthesized quantity | Final value |
| --- | --- |
| Shoulder crank / rod / rocker | **11.82 / 20.57 / 24.78 mm** |
| Elbow crank / rod / horn | **12.34 / 114.47 / 21.07 mm** |
| Shoulder / elbow crank mounting phases | **11.98° / 62.04°** |
| Rocker-to-wing / horn-to-wing offsets | **−67.28° / 134.64°** |

The result achieves **−21.54° to +36.12° shoulder motion** and **14°–65° elbow bend**, with minimum transmission angles of **40.50° in both drives**. The shoulder RMS error is **4.84°** and elbow upstroke RMS error is **6.9977°**, just below its 7° cap. These near-binding transmission and tracking limits explain why the solution does not reach the originally desired −30° shoulder position or 70° fold. Physical packaging was checked separately: the original **3 mm-link layout** had no modeled collisions over **1,440 poses**; the intended **6.35 mm plywood layout remains unverified**.

### Choice and justification

**We chose the direct six-bar** because it reduces the shoulder ground distance from **50 to 28 mm**, reduces the two-wing gear count from **six to two**, and increases achieved peak folding from **50.47° to 65°** while retaining transmission above **40°**. Sharing the input shaft eliminates the separately geared elbow crank at the shoulder, better supporting the compact bat-like body. The tradeoff is less transmission margin and imperfect tracking of the revised targets. The chosen package retains separated depth layers: a later same-face arrangement collided and was rejected. Thicker-stock packaging and actuator selection remain outstanding.

The analytical seeds, final parameters and assembly conventions are saved in `outputs/dimensions.json`, `outputs/compact/dimensions.json` and `outputs/direct/dimensions.json`. The corresponding synthesis implementations are `src/rmd/legacy_geared_synthesis.py` and `src/rmd/direct_drive.py`, with numerical inputs in `config/`. These files provide the full-precision values and calculations needed to reproduce and check the reported results; the numerical search does not establish a global optimum.
