# Physical phantom integration (research only)

The controller core accepts the exact 22-D normalized observation and a
nonnegative current-force signal. The platform team should implement
`interfaces/robot_interface.py`, `interfaces/observation_adapter.py`, and
`interfaces/force_interface.py`; TD-MPC2 internals and fuzzy rules should
remain frozen until a separate validation protocol authorizes changes.

| Algorithm component | Current simulation source | Physical platform requirement |
|---|---|---|
| Five guidewire points | stEVE Tracking2D, ordered distal first | Calibrated tracking with stable ordering, visibility/confidence, and compatible episode normalization |
| Target position | stEVE Target2D | Registered target in same projection and normalization frame |
| Device rotation | stEVE device angle | Measured/calibrated rotation in radians and sine/cosine conversion |
| Vessel geometry/centerline | AorticArch BranchWithRadii | Registered vessel model with local radii and uncertainty estimate |
| Wall-clearance proxy | 3-D wire-to-centerline/radius query | Reproduce/validate signed proxy for first three distal samples; it is not exact collision distance |
| Insertion command | normalized `a_v` to ±50 mm/s | Calibrated velocity mapping, limits, interlocks, watchdog, and stop behavior |
| Rotation command | normalized `a_omega` to ±3.14 rad/s | Calibrated mapping and limits; fuzzy filter must leave it unchanged |
| Current force | SOFA distal 3-mm reconstructed reaction | Validated force sensor, proximal-force estimate, motor-current estimate, or other platform-specific signal |
| Force prediction input | G13 22-D observation + nominal action | Same feature conventions and action normalization as training |
| Control frequency | 7.5-Hz RL interval, 22 × 0.006-s SOFA steps | Deterministic timing/latency budget and timestamp alignment; characterize different physical rate before use |

The simulation `F_lim` and fuzzy force memberships are not transferable by
unit label alone. A proximal sensor, motor-current estimate, and distal SOFA
reaction measure different quantities. Physical calibration must establish
scale, offset, dynamics, saturation, noise, latency, and their relationship to
contact events. Select a physical operating envelope through a separate
approved phantom protocol. Never call the simulation Q95 a clinical injury
threshold.

Recommended integration order:

```text
tracking adapter → 22-D observation reconstruction → nominal TD-MPC2
→ robot action adapter → force interface → fuzzy safety filter
```

Start in shadow mode: record observations, nominal/safe actions, force, and
timing without actuating from the controller. Verify registration and
normalization on held-out phantom trajectories. Then validate action limits,
watchdogs, emergency stop, and force measurement independently before any
closed-loop phantom run. Human supervision and institution-approved hardware
safety processes are required; this repository does not provide them.
