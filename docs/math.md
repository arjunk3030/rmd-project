# Math and design flow

The two options share editable target samples and the same length units (mm).
Targets are periodic shape-preserving PCHIP curves; they are stylized guesses,
not measurements. A constant-speed motor angle theta spans0..2pi per cycle.
Positive fold F gives outer angle alpha-F. Both wings are mirrored; the two O
shafts rotate oppositely through an equal external gear pair.

## Compact geared four-bars

A has body-fixed pivots O and S. Its crank radius a, connecting rod b and rocker c
satisfy the usual loop closure. In a reference frame with O–S ground length d:

    K1 cos(psi) - K2 cos(phi) + K3 = cos(phi-psi)
    K1=d/a, K2=d/c, K3=(a²-b²+c²+d²)/(2ac)

Three input/output pairs give a3×3 linear system for K1,K2,K3. Recover a=d/K1,
c=d/K2 and b²=a²+c²+d²-2acK3. Mounting offsets and assembly branch are searched;
three-point interpolation is a seed, not a guarantee of good full-cycle motion.
Joint least-squares and constrained SLSQP refine the complete cycle. The actual
rocker direction is alpha+kappa.

B uses the moving inner wing S–E as its reference link. Its local crank input is
`u2=-theta+delta-alpha`; its horn output is `eta-F`. Equal O–S gears provide the
counter-rotation. A's rocker/inner wing is bearing-mounted independently of the
S shaft that drives B. This independence is essential.

The actual compact layout keeps d=50 mm and rotates A about S by rho. It adds rho
to the input crank zero and rocker-to-wing mounting offset; alpha is unchanged.
For shoulder half-spacing h and equal drive-gear pitch diameter D:

    O_local=[D/2-h, -sqrt(d²-(D/2-h)²)]
    rho=atan2(O_local.z,O_local.y)-atan2(O_reference.z,O_reference.y)

This is rigid layout placement, not a second link-length synthesis.

## Small-body direct coupled six-bar

Both input arms belong to one supported O shaft. The front arm drives the
shoulder and the rear arm drives the outer-wing horn Q through a rod. The motor
is in the stand: equal 20T pulleys and a timing belt drive right O, then equal
34T gears reverse left O. There is no second driven input at S.

The direct ground is now 28 mm, independent of the geared 50 mm reference.
With 50 mm shoulder spacing and 34 mm gear centers, local O=[-8,-sqrt(28²-8²)]
and S=[0,0]. Inner/outer wing lengths are 100/150 mm. These are chosen package
inputs. Ten synthesized variables are a1,b1,c1,kappa,phase_A,a2,phase_B,horn,eta,rod.

    A=O+a1 [cos(theta+phase_A),sin(theta+phase_A)]
    |B-S|=c1, |B-A|=b1
    alpha=atan2(B.z,B.y)-kappa
    E=100 [cos(alpha),sin(alpha)]
    D=O+a2 [cos(theta+phase_B),sin(theta+phase_B)]
    Q_desired=E+horn [cos(alpha-F_target+eta),sin(alpha-F_target+eta)]
    TIP=E+150 [cos(alpha-F),sin(alpha-F)]

The user-proposed shoulder +35/-30 degrees and fold 15..70 degrees transform
the shared PCHIP timing curve. They replace straight-on-downstroke targets.
Bounded least squares supplies candidate lengths and phases; constrained SLSQP
uses actual circle closure to refine the joint motion. Shoulder sweep can relax
because the user prioritizes a small body and transmission >=40 degrees. Solver
margin is 40.5 degrees; independent dense checks enforce 40 degrees. Target
errors and actual extrema remain visible rather than substituting target curves
for solved motion. This is numerical function synthesis, not an exact three-pair
Freudenstein solution. A numerical seed records the previous fitted solution.

Actual Q is a fixed-side circle intersection centered at E and D, with radii
horn and rod. Actual F=alpha+eta-atan2(Q-E). The effective ground O-E moves, so
ordinary independent-four-bar Grashof is inappropriate for the elbow loop.
Circle closure and full-cycle transmission are checked directly. The shoulder
loop uses its actual 28 mm ground in its Grashof test.

Plain bushings and 3 mm shafts replace the large motor/bearing package. Their
chosen envelope sizes do not certify wood strength, clamp grip or running fit.
The stationary actuator reservation is outside the measured bat body. Body size
checks include crank/hardware sweep, gears, frame and face, while outgoing wing
links and the stand are reported separately.

## Assembly, transmission and clearance

For circle centers separated by r and radii c,b:

    x=(c²-b²+r²)/(2r), h²=c²-x²
    intersection=center+x*e +/- sqrt(h²)*perpendicular(e)

One signed branch is kept throughout the entire cycle. Negative h² is an invalid
assembly, even though optimizer trial residuals clip the square root to remain
finite. The full-cycle validator rejects invalid closure or non-rigid lengths.
Transmission is the acute equivalent angle between the coupler and output
rocker/horn, required to be at least40°. Both loop angles and periodic closure
are recomputed on fresh samples; saved PASS flags are not trusted.

The physical3D geometry has actual axial lap planes, shafts, hubs and frame/motor
envelopes. Capsule and segment/triangle distance tests include panel thickness;
only named shared joints, bores and intended skin-support contacts are excluded.
The direct fabric panels use 10 mm hinge relief and 20 mm root relief with
smaller joint housings. Direct inner rib roots start 20 mm out from the shoulder.
The direct panels face forward so the rear rod stays outside the skin.
Gear vertex penetration is checked over sampled tooth phases; theoretical
contact ratio and standard undercut conditions are also screened. Direct crank arms are separate from the gears. Their pin-hole ligaments and
small shaft-hub engagement are checked geometrically; torque transfer is unverified.

These are sampled nominal checks, not toleranced solid CAD or loaded deflection
certification. Subtracting finite material around every joint is not implied by
an envelope assembly drawing; use the drilling/part profiles and bought-hardware
fit checks before fabrication.

## Load estimate

For member masses m and centers r(theta), uniform-rod inertia gives

    V=sum(m*g*z)
    I_eff=sum(m*|dr/dtheta|² + I_center*(dangle/dtheta)²)
    motor_torque=V' + 0.5*omega²*I_eff'

Both wings are included. A guessed friction allowance,2-second acceleration
allowance, mesh efficiency and service factor give a running-torque target.
Outer-wing gravity/inertia and elbow translation estimate rod force through the
actual horn lever arm. A conditional steel-axle bending/deflection estimate and
ideal printed-rod Euler buckling check are reported. Material and mass values
are assumptions; no full pin/bearing/tooth, aero, impact or fatigue proof follows.
The motor's holding rating is not substituted for running torque.
