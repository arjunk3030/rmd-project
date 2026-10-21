## 1. The task in numbers

Our mechanism must flap two mirrored, two-segment wings and mechanically coordinate their elbow folding using **one actuator**. It is a stationary bat-like display, not a flying robot. Each wing has a **100 mm inner segment** and a **150 mm outer segment**. One input-shaft revolution produces one wingbeat. The nominal operating speed is **15 rpm**, corresponding to **0.25 Hz** or **4 seconds per wingbeat**.

### Desired motion and timing

The **shoulder angle, α**, is the inner-wing angle relative to outward horizontal; positive angles raise the wing. The **elbow bend, F**, is the downward fold of the outer wing relative to the inner wing; **F = 0° means a straight wing**. The outer-wing angle relative to horizontal is α − F.

The desired shoulder range is **−30° to +35°**, and the desired elbow bend is **15°–70°**. The wing should be more extended during the downstroke and fold most strongly near mid-upstroke. The following estimated targets define the motion; smooth interpolation supplies the intermediate poses.

| Time in cycle (s) | Input angle (°) | Shoulder target α (°) | Elbow bend target F (°) |
| --- | ---: | ---: | ---: |
| 0.0 | 0 | +35.00 | 30.40 |
| 0.5 | 45 | +25.51 | 18.85 |
| 1.0 | 90 | +2.50 | 15.00 |
| 1.5 | 135 | −20.51 | 18.85 |
| 2.0 | 180 | −30.00 | 30.40 |
| 2.5 | 225 | −20.51 | 57.35 |
| 3.0 | 270 | +2.50 | 70.00 |
| 3.5 | 315 | +25.51 | 57.35 |
| 4.0 | 360 | +35.00 | 30.40 |

The first **2 seconds** are the nominal downstroke; the following **2 seconds** are the nominal upstroke. These are aesthetic targets rather than measured bat kinematics, and exact passage through every target is not required. Shoulder RMS error must be **no greater than 6° over the cycle**, and elbow-bend RMS error must be **no greater than 7° over the nominal upstroke**. Both transmission angles must remain **at least 40° throughout the cycle**, with continuous assembly on fixed branches. These mechanical requirements take priority over matching the target extrema exactly.

### Output load and torque

The mechanism must lift and accelerate both wing assemblies. For preliminary sizing, we consider a complete mass of **48–150 g per wing**, including its frame, film and wing hardware. This corresponds to a gravitational force of approximately **0.47–1.47 N per wing**. These are assumed sizing cases; completed wing masses must be measured before final actuator selection.

Using an assumed inner-to-outer mass split of **28:20**, with each segment's center of mass at its midpoint, a straight horizontal wing produces approximately **0.048–0.150 N·m gravitational moment about the shoulder**. The outer segment produces approximately **0.015–0.046 N·m about the elbow**. These values specify the output-load scale in a reference pose, not peak dynamic joint torques.

### Size and construction requirements

| Requirement | Value |
| --- | --- |
| Central body envelope | At most **76 mm wide × 80 mm high × 80 mm deep** |
| Envelope scope | Central mechanism only; excludes outgoing wing links and stationary stand |
| Left-to-right shoulder spacing | **50 mm** |
| Inner / outer wing lengths | **100 mm / 150 mm** per wing |
| Maximum straight horizontal wingspan | Approximately **550 mm** |
| Shoulder-to-input-shaft spacing, O–S | **28 mm** per wing, chosen layout input |
| Input-shaft spacing across the body | **34 mm**, chosen layout input |
| Required nominal clearance | At least **1 mm** between non-contacting modeled parts |
| Intended link stock | **¼-inch plywood, 6.35 mm thick** |
| Wing covering | Thin plastic film; final thickness and mass to be established |

### Actuator requirement

The mechanism must operate with **one continuously rotating actuator** driving both wings. The selected drive architecture uses a **1:1 timing belt** to drive one input shaft and an equal external gear pair to reverse the opposite shaft. The shoulder and elbow crank arms on each wing are rigidly coupled to their input shaft.

The proposed actuator type is a **speed-controlled geared DC motor or suitable continuous-rotation servo**, operating at approximately **15 rpm under load**. Preliminary both-wing sizing gives a motor-output torque requirement of approximately **0.36–0.77 N·m** across the assumed mass cases. This estimate includes gravity and inertia, an aggregate friction allowance of **0.05 N·m**, **95% assumed transmission efficiency**, a **2-second startup ramp**, and a **3× service factor**. Aerodynamic loads and binding are not included.

A provisional selection range is **0.5–1.0 N·m of usable running torque at 15 rpm**, with the final actuator required to meet the recalculated load requirement for the actual masses. **No specific actuator has been selected.** A stall-torque rating alone does not establish running capacity, and a standard limited-angle positional servo cannot directly execute the required continuous input rotation.

The values above describe the task and its current sizing assumptions. Compliance of the intended **6.35 mm plywood construction** remains to be checked; the existing passing clearance model uses **3 mm links**.
