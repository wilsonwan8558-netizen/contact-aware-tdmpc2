# Collaborator handoff

1. **Included:** frozen G13 22-D nominal planner/force-head architecture,
   G16.1 fuzzy filter, the matching Generic stEVE runtime, configs, interfaces,
   docs, demos, and tests.
2. **Excluded:** the 63-MB checkpoint, all G-series experiment logs/runs,
   training scripts, failed models, G15 controller, G16.2 withdrawal, and
   hardware-specific actuation.
3. **Checkpoint:** approved G13 `step_260000.pt`, SHA256
   `b2bba8be2e2722886c20952b15712deaa31ab612825999f1b3469a34fd6ef7be`.
   Supply via `--checkpoint`; do not commit it.
4. **Simulation demo:** follow README installation, then run
   `python scripts/run_nominal_demo.py --checkpoint /path/to/step_260000.pt`.
5. **Safety demo:** run
   `python scripts/run_fuzzy_safety_demo.py --checkpoint /path/to/step_260000.pt`.
6. **Physical files to implement:** `contact_aware_tdmpc2/interfaces/robot_interface.py`,
   `observation_adapter.py`, and `force_interface.py`; use the non-actuating
   `examples/phantom_integration_skeleton.py` as a starting boundary. Pass the
   robot and an independent force interface to `shadow_step()`.
7. **Required signals:** the robot supplies five ordered tracking points,
   target, device rotation, registered vessel centerline/radii, and timed
   insertion/rotation command feedback; the separate force interface supplies
   a validated force estimate via `read_force()`.
8. **Simulation-specific assumptions:** Generic-SOFA constraint forces,
   distal 3-mm reaction, episode-specific 2-D normalization, synthetic vessel
   geometry, ±50 mm/s and ±3.14 rad/s action mapping, 7.5-Hz control.
9. **Physical calibration remaining:** observation registration/normalization,
   force scale/dynamics/latency, robot velocity limits, emergency stop,
   control timing, and a new platform-specific risk threshold.
10. **First integration steps:** tracking adapter → observation reconstruction
    → nominal inference → robot action adapter → force interface → fuzzy
    filter, beginning with shadow-mode validation.

Do not share with Weibo until Wilson and Prof. Sun approve license and
redistribution, checkpoint transfer, third-party notices, and physical-safety
scope. No remote or public repository is created by this handoff.
Before simulation, run `python scripts/check_environment.py` (optionally with
`--checkpoint /path/to/step_260000.pt`) to check SOFA, CUDA, the bundled `eve`
origin, and checkpoint hash. Its checks do not replace physical calibration.
