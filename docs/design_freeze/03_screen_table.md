## 3. Screen of the chosen design

**Main mechanism:** One Stephenson six-bar per wing, mirrored and driven by one actuator. The chosen package is the original direct layout, not the colliding same-face experiment.

**Sizing method:** Joint bounded least-squares initialization followed by constrained SLSQP optimization of six lengths and four mounting/phase angles.

**Check scope:** Motion and geometry were checked at **1,440 poses, every 0.25° of input rotation**. Additional motion calculations at **7,200 poses, every 0.05°**, provide the extrema and input angles below. Clearances refer to the **3 mm-link model**; the intended **6.35 mm plywood package is not yet validated**. Input angles use the saved solver/animation zero.

| Check | Our numbers and how we checked | Assessment |
| --- | --- | --- |
| **Task in numbers** | Desired shoulder range **−30° to +35°**, elbow bend **15°–70°**, one revolution per **4 s** at **15 rpm**. Achieved shoulder **−21.54° to +36.12°**, elbow **14.00°–65.00°**. Shoulder RMS error **4.8364° ≤ 6°**; nominal-upstroke elbow RMS error **6.9977° ≤ 7°**. Calculated by comparing solved motion with the target curves. | Meets the adopted error and relaxed range limits; does not hit the original target extrema exactly. |
| **Assembly and branch** | One fixed branch for each closure throughout **360°**. Maximum fixed-link-length error **4.3 × 10⁻¹⁴ mm**; cycle-closure error **8.0 × 10⁻¹⁵ mm** in the 1,440-pose report. Circle-intersection and periodic-closure checks detect invalid assembly. | Numerical PASS. Roundoff-scale errors indicate mathematical closure, not physical manufacturing accuracy. |
| **Order** | As input angle increases, shoulder top occurs at **13.65°**, minimum fold at **96.25°**, shoulder bottom at **181.65°**, and maximum fold at **247.15°**. The wing therefore extends during the downstroke and reaches maximum fold during the upstroke. Checked from the full-cycle angle traces at 0.05° spacing. | Intended event order retained; actual phases differ from the ideal target phases. |
| **Grashof class and drive** | Shoulder links: **11.816, 20.574, 24.775 and 28.000 mm**. Shortest + longest = **39.816 mm < 45.349 mm**, a **5.533 mm margin**. The shortest link is the input, adjacent to ground: **Grashof Class I crank–rocker**. Complete six-bar assembly checked separately through **360°**. | PASS for continuous input. Ordinary four-bar Grashof classification does not independently classify the elbow loop. |
| **Transmission angle** | Shoulder minimum **40.50084° at input 61.40°**. Elbow minimum **40.50090° at input 242.50°**. Recomputed at **0.05° input increments** over the full revolution. Required minimum is **40°**. | Sampled numerical PASS in both loops. |
| **Motor range and torque** | Required input is continuous **360° rotation at 15 rpm**. For assumed complete wing masses of **48–150 g each**, the preliminary 6.35 mm-link estimate is **0.36–0.77 N·m at the actuator output for both wings**, including friction, estimated losses and a **3× service factor**. Proposed actuator type: one geared DC motor or continuous-rotation servo. | **Unresolved:** no specific motor selected or running torque verified. Masses and friction are assumptions; aerodynamic loading is omitted. |
| **Pivots and packaging** | Ground pivots per wing: **S = (0, 0), O = (−8, −26.833) mm**; ground length **28 mm**, shoulder spacing **50 mm**, input-shaft spacing **34 mm**. Original audited central envelope: **74 mm wide × 80 mm high × 76 mm deep**, including the small face still present in the audit configuration. **0 modeled conflicts** over **1,440 poses**; reported minimum nonadjacent-part clearance **2.022 mm**, above the **1 mm** requirement. | Nominal PASS for **3 mm stock**. **6.35 mm stock and actual hardware fits remain unverified.** Envelope excludes outgoing wings and stand. |
| **Unwritten requirements** | Bat-like appearance assessed with **100/150 mm wing segments** and a **550 mm maximum straight horizontal span**. Panel geometry includes **20 mm root relief** and **10 mm hinge relief**. These provide geometric checks, but the motion objective does not quantify visual resemblance, flexible-film behavior, wood wear or assembly access. | **Judgement / prototype test required.** Film thickness, tension and hardware access are not physically verified; the cartoon costume is appearance-only. |
| **Active limit** | Both transmission minima sit approximately **0.0009° above the 40.5° solver floor**. Peak fold is approximately **65.0007°**, near its **65° lower bound**. Upstroke elbow RMS error is **6.9977°**, only **0.0023° below its 7° cap**. These are numerically near-binding constraints in the saved solution. | Improving one motion feature may worsen another or violate a constraint. The original package also reaches its **80 mm body-height limit**; body size was screened separately, not minimized by the motion objective. |

### Link lengths

| Dimension | Length (mm) |
| --- | ---: |
| Ground O–S | 28.000 |
| Shoulder crank O–A | 11.816 |
| Shoulder connecting rod A–B | 20.574 |
| Shoulder rocker S–B | 24.775 |
| Elbow-drive crank O–D | 12.341 |
| Elbow connecting rod D–Q | 114.468 |
| Outer-wing horn E–Q | 21.070 |
| Inner wing S–E | 100.000 |
| Outer wing E–T | 150.000 |

These dimensions describe segments of six rigid bodies, not nine independent links. Both crank arms are rigidly attached, the rocker is rigid with the inner wing, and the horn is rigid with the outer wing. Rounded dimensions are for reporting; assembly phases and full-precision parameters are in `outputs/direct/dimensions.json`.

### Mechanism level

**Level 2 is demonstrated:** the mechanism was sized by numerical synthesis from a stated motion task and checked over its complete motion. A proposed Level 3 argument is that the elbow dyad replaces an independently actuated elbow while a single actuator coordinates both mirrored wings. The instructor's Level 3 definition should be confirmed before claiming it; two independently controlled actuators could reproduce the shoulder/elbow trajectories, so we do not claim that this is impossible.

### Remaining risks

The two main unresolved items are **repackaging and checking the intended 6.35 mm plywood construction**, and **verifying the wing masses and selecting an actuator with sufficient running torque**. The same-face experiment is not the chosen design: it has rod-to-pin interference. Numerical PASS for the original package is not a fabrication or loaded-operation certification.
