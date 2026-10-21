# Simulation distal-force signal

The frozen Generic-SOFA scene uses `GenericConstraintSolver`,
`ProjectedGaussSeidel`, tolerance `1e-4`, `maxIterations=2000`, and
`computeConstraintForces=True`. Contact response is
`FrictionContactConstraint` with `mu=0.001`; SOFA substep `dt=0.006` s.

At the end of each substep, the passive monitor reads the Generic solver's
active `constraintForces` multipliers and the current guidewire collision
Jacobian. The distal region is the first **approximately 3 mm** of wire,
measured along the collision-edge chain from its distal tip. A line contact
at the 3-mm boundary is included as a whole triplet. Contact normal and two
tangent rows are grouped; their Jacobian vectors and multipliers produce a
vector reaction. For selected distal contacts:

```text
F_distal = || Σ_c J_c^T lambda_c / dt ||_2
```

The resultant is a **vector sum**, not a sum of scalar magnitudes. The monitor
checks row/group counts and nonfinite values. One RL interval is `1/7.5` s;
the simulator executes `int((1/7.5)/0.006) = 22` SOFA substeps. The per-RL-step
force used by the filter is:

```text
F_t = max over the 22 substeps of F_distal
```

The next step receives the previous interval's `F_t`; the episode begins
with `F_t=0`. `F_lim=3.685331040756903` was the Q95 value from the frozen
Generic-SOFA force baseline under this scene and unit convention. Values are
**nominal simulation N**. This is a statistical reference, **not a clinical
injury threshold**. A physical force sensor, proximal-force estimate, or
motor-current-derived estimate must be calibrated and independently validated;
do not directly transplant this `F_lim` to physical hardware.
