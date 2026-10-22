# Post-Audit Repository Hardening

Date: 2026-10-22. These changes address the requested P1/P2 handoff issues
without changing the frozen G13 planner, force predictor, G16.1 fuzzy
calculation, action mapping, SOFA force formula, or any numerical constant.
The prior share-readiness audit remains a historical snapshot. No commit,
checkpoint copy, dependency installation, hardware command, or push was made.

## Files changed

| Area | Files | Change |
|---|---|---|
| Runtime/config checks | `contact_aware_tdmpc2/runtime_checks.py` (new), `safety/fuzzy_inference.py`, `env/g13_env.py`, `env/steve_env.py` | Verify the bundled `eve` origin and reject YAML/implementation drift before controller or Generic-SOFA startup. |
| Collaborator entrypoints | `scripts/run_nominal_demo.py`, `run_fuzzy_safety_demo.py`, `compare_nominal_vs_safety.py`, `inspect_force_signal.py`, `check_environment.py` (new), `examples/minimal_inference.py` | Fail fast on wrong `eve`, give a read-only environment preflight, and make the inference example runnable from the root before installation. |
| Checkpoint error | `contact_aware_tdmpc2/tdmpc2/checkpoint.py` and checkpoint-taking entrypoints | Missing file now gives an intentional-exclusion explanation, exact filename/SHA256, and `--checkpoint` usage rather than an unexplained raw traceback. |
| Physical API | `interfaces/robot_interface.py`, `examples/phantom_integration_skeleton.py` | `RobotInterface` no longer owns force acquisition; shadow-mode `shadow_step(controller, robot, force_interface, observation_adapter)` reads the independent `ForceInterface.read_force()` and never sends an action. |
| Tests | `tests/test_observation.py`, `test_runtime_checks.py` (new), `test_physical_interfaces.py` (new), `test_controller_api.py` (new), `test_missing_checkpoint.py` (new) | Full 22-index ordering, wrong/correct `eve` origin, frozen config/mirror tampering, force-interface separation/no actuation, checkpoint-free diagnostics, and concise missing-file CLI error. |
| Documentation | `README.md`, `COLLABORATOR_HANDOFF.md`, `docs/PHYSICAL_DEPLOYMENT.md`, `docs/SHARING_AUDIT.md`, this file | Explain preflight and authority/mirror rules, independent robot/force contracts, and correct stale pre-initial-commit tense without erasing historical results. |

`contact_aware_tdmpc2/interfaces/force_interface.py` remains the independent
`read_force()` protocol; its existing contract did not need a code change.

## Frozen-value authority and checks

The frozen implementation values are authoritative; root `configs/*.yaml`
and packaged `contact_aware_tdmpc2/configs/*.yaml` are reviewed mirrors, not
runtime tuning knobs. `runtime_checks.py` locks force and clearance quantiles,
`F_lim`, `rho_0`, input/output membership descriptors, all ten rule identities
and contents, and the 0.001/1001-point grid. `FrozenFuzzyRisk` also checks
its existing inference mode and compares YAML `rho_0` with the actual filter
constant. Before constructing a G13 scene, `GeometryForceEnv` checks the
bundled `eve` origin and validates packaged/root simulation YAML against
implementation SOFA dt 0.006 s, friction 0.001, and 22 substeps. The live
`assert_generic_scene()` check remains the authority for actual SOFA solver
components after reset. Mismatch raises an error; it never silently changes
the algorithm.

## Checks run

- `python -m pytest -q -rs` in `steve_tdmpc`, using cached pytest 7.1.2 on
  `PYTHONPATH` because pytest is not installed in that conda environment:
  **13 passed, 1 skipped, 0 failed**. The skipped test needs the intentionally
  unbundled approved checkpoint (`CONTACT_AWARE_CHECKPOINT`).
- `python scripts/run_nominal_demo.py --help`,
  `python scripts/run_fuzzy_safety_demo.py --help`, and
  `python examples/minimal_inference.py --help`: all exit 0 from the root,
  without a checkpoint or package installation.
- `python scripts/check_environment.py` in the plain shell: expected **FAIL**
  (5 FAIL, 4 WARN). Python 3.10 and PyTorch 2.7.1+cu128 were present, but CUDA
  was not visible, and that shell lacked SOFA/SofaRuntime and their root vars.
- The same preflight in `steve_tdmpc`: **FAIL** (2 FAIL, 2 WARN). Bundled
  `eve`, `Sofa`, BeamAdapter, Python/PyTorch/CUDA-runtime versions, and SOFA
  paths passed; the current execution environment did not expose a CUDA
  device. Both warnings are the intentionally absent checkpoint path/hash.
- `git diff --check`: passed. Only intended source/docs/tests are modified;
  the prior untracked `docs/SHARE_READINESS_AUDIT.md` was preserved unchanged.

## Remaining limitations and release gates

1. The approved G13 checkpoint is still absent. Full checkpoint loading,
   controller inference with its real weights, CUDA rollout, and Generic-SOFA
   episode behavior were **not** rerun. This is a remaining P1 validation task
   once authorized access is available, not a license to copy the file.
2. `environment.yml` remains a Python/pip scaffold. The exact external SOFA
   23.06/SofaPython3/BeamAdapter binary and NVIDIA driver setup still needs a
   collaborator-tested installation recipe (remaining P1).
3. This execution environment reported no visible GPU, so its CUDA preflight
   failed; this does not establish whether the host has a suitable GPU outside
   the sandbox. Physical force calibration, observation registration, timing,
   action limits, interlocks, and phantom shadow-mode validation remain
   platform-specific work. The skeleton is intentionally non-operational.
4. Root licensing, third-party approval, and checkpoint-transfer approval
   are unchanged P0 release gates. No approval or redistribution is implied.

Behavior-affecting changes are limited to **fail-fast validation and clearer
errors** when imports/configuration/checkpoint are invalid. Valid frozen
G13/G16.1 numerical behavior is unchanged. The physical example's call
signature changed to require a separate force interface; it still never
actuates hardware.
