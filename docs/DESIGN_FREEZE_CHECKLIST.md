# Design freeze preparation checklist

Assignment reviewed 20 October 2026: Design_Freeze_21Oct-1.pdf, three pages.

## Submission requirements

One submission per team. Due Wednesday 21 October at 8:00 am on Canvas:

- Team##_Freeze.pdf: report covering the task in numbers, at least two synthesized candidates, numerical screening, mechanism level, and two risks with actions.
- Completed screen table from assignment page 3. Page 1 says at most four report pages plus the screen table; the rubric also says within four pages. Safest layout: include the screen within four total pages if it remains readable, or clarify the extra-page allowance.
- Team##_synthesis.py or .ipynb: runnable synthesis code. If submitting a wrapper for the modular project, include all dependencies/source/configuration it imports; do not submit a wrapper alone.
- Team##_slide.pdf: one slide with team, numerical task, chosen linkage, key dimensions, method and level.
- Team##_animation.mp4 or .gif: full motion with targets marked, consistent with report. HTML viewers alone do not satisfy the requested format.
- Two-minute presentation in class, followed by one question.

Due Monday 26 October:

- By 8:00 am: approximately 20-second hand-operated mock-up video, Team##_mockup.mp4, plus one paragraph explaining what was learned and whether anything should change.
- Bring the physical mock-up to class. Its dimensions should be close to the synthesized design. Report any changes discovered through the physical build.

The freeze report is 75 points, presentation 10 and mock-up 15. Level 2 or 3 is the acceptance gate. A below-Level-2 report is returned for resubmission within 48 hours and capped at 50/75.

## Recommended candidates

Use the existing compact geared design and direct Stephenson six-bar as the two main synthesized candidates. Both have saved dimensions, methods and nominal checks. State clearly that their target curves evolved, so these are historical alternatives and not an equal-target optimization benchmark.

| Candidate | Minimum transmission A / elbow | Peak elbow bend | Gear count | Saved nominal conflicts |
| --- | --- | --- | --- | --- |
| Older compact geared | 50.24° / 44.10° | 50.47° | 6 | 0 |
| Preferred direct Stephenson | 40.50° / 40.50° | 65.00° | 2 | 0 |

The direct version also uses a belt from the stand. Do not call it gearless or beltless. The same-face version can illustrate a rejected packaging attempt, but it is not a separately synthesized candidate: it reuses the direct lengths and has interference.

## Main unresolved decision

The current passing direct model uses 3 mm plywood. The confirmed intended stock is 6.35 mm plywood with thin plastic film. That thickness change is not yet packaged or revalidated. Do not claim the passing 3 mm clearance report applies to the thicker build.

Preferred next work: preserve the old package, implement a separate 6.35 mm package, update joint spacers/fasteners/shaft supports, and check it. If not completed, report the material discrepancy explicitly as an unresolved packaging risk rather than claiming a fully frozen build. An actuator model also remains unselected.

## Four page report outline

1. Task and candidate comparison: chosen motion ranges/timing, allowable errors, size, materials, load assumption, actuator type, and numerical comparison of both candidates.
2. Synthesis: labeled six-bar figure, rigid-link count, unknown vector, loop-closure equations, objective and hard constraints, resulting lengths/phases, and why direct was chosen.
3. Completed nine-row screen with numbers and computation method. Distinguish PASS, FAIL and unresolved hardware judgement.
4. Chosen dimensioned layout, mechanism level, active constraints, and the two biggest risks with concrete actions.

Use desired motion and achieved motion in separate columns. Do not claim that the current direct result meets the original −30° shoulder or 70° maximum fold targets exactly.

## Screen evidence and missing items

| Assignment row | Available evidence or action |
| --- | --- |
| Task in numbers | Targets: shoulder −30° to +35°, bend 15°–70°, peak near mid-upstroke. Give adopted acceptance limits and achieved ranges separately; include speed, size, load and actuator. |
| Assembly and branch | Fixed branches in saved direct solve; link-length error below 5e−14 mm and cycle closure below 1e−14 mm in saved nominal report. State branch choices and sampling. |
| Order | Give a small crank-phase table of shoulder/bend and demonstrate downstroke then upstroke. Peak fold is at 247.25°. Do not replace this row with a generic PASS. |
| Grashof and drive | Shoulder: shortest + longest = 39.816 mm < 45.349 mm, shortest input adjacent to fixed ground; crank–rocker. Six-bar closure checked separately. |
| Transmission | Fresh 7,200-pose check at 0.05° spacing: shoulder minimum 40.50084° at crank 61.4°; elbow minimum 40.50090° at 242.5°. Crank zero is the saved animation/solver zero. |
| Motor range and torque | Continuous 360° input, 15 rpm display speed. Provisional both-wing requirement about 0.36–0.77 N·m over assumed complete wing masses of 48–150 g each with 6.35 mm links. This is a scenario estimate, not selected-actuator capacity. State masses, efficiency, service factor and omissions. |
| Pivots and packaging | Original 3 mm layout: 50 mm shoulders, 34 mm input centers, 28 mm O–S, no modeled conflicts at 1,440 poses. 6.35 mm stock is not yet validated. Same-face option fails rod-to-pin clearance. |
| Unwritten requirements | Bat-like appearance, film slack/tension, wood wear, assembly access and manufacturability. Say which are not in the motion objective and give a numerical proxy or inspection scope where possible. |
| Active limit | Transmission constraints near 40.5° solver floor, maximum bend near the imposed 65° lower peak bound, and elbow upstroke RMS 6.9977° near the 7° cap. These limit further target matching in this solution; do not claim global optimality. |

## Mechanism level wording

Level 2 is supported by numerical synthesis from a stated task followed by checks. A Level 3 argument is that the added dyad mechanically coordinates shoulder and elbow, replacing a separately actuated elbow while the geared mirror coordinates the opposite wing.

There is a wording difference in the assignment: page 1 asks what two actuators alone could not do, while the rubric awards Level 3 for a job that otherwise needs another actuator. Do not claim two independently controlled actuators are incapable of reproducing shoulder and elbow trajectories. Use the defensible actuator-replacement argument and clarify the intended interpretation if needed. The exact 14 October level sheet has not been supplied here.

## Presentation and video

Use the labeled mechanism, not only the cartoon bat. The current 2D view identifies joint letters and rigid triangles, but target poses/curves still need to be added to a submission animation. Export an MP4 or GIF and watch the exact submitted file through a full cycle. Do not use the known-clashing same-face version as the chosen design animation.

Suggested two-minute talk: 20 seconds task; 25 seconds candidate choice; 35 seconds synthesis; 25 seconds animation and screen; 15 seconds level and risks.

## Highest priority work

1. Resolve and verify the 6.35 mm physical package or explicitly document its unresolved status.
2. Establish plausible complete wing masses and actuator choice; fix the omitted crank2_direct mass term before production load-report regeneration.
3. Prepare a reproducible synthesis submission with configurations and environment instructions.
4. Assemble the report and numerical screen, then the single slide and target-marked video.
5. Watch the exported video, cross-check every reported dimension against the chosen design, and prepare answers about the active limits and material assumptions.

Reporting an observed problem honestly is explicitly accepted by the assignment; leaving checks missing is penalized. Do not turn a known failure into a PASS for presentation.
