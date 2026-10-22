# Share Readiness Audit

Audit date: 2026-10-21. Scope: the local `contact-aware-tdmpc2` checkout on
`main` at `718a68c`. This was an inspection and non-mutating test audit; no
checkpoint was copied, no hardware was driven, and no full SOFA episode was run.
“Share” below means the proposed external collaborator handoff, not continued
internal review. Findings describe the repository as inspected, not a legal or
clinical-safety determination.

## Executive Summary

**NOT READY for external collaborator share.** The frozen G13/G16.1 method is
coherent in the inspected source, and the tracked tree is compact and free of
detected secrets or research-run data. Two handoff gates remain open: approval
of redistribution/licensing, and an approved way to provide the exact G13
checkpoint. The latter is intentionally absent from Git, so this audit could
not independently rerun checkpoint-dependent inference or simulation. Internal
documentation and adapter work may continue, but neither the repository nor
the checkpoint should be transferred until the responsible people clear those
gates. **P0: 2; P1: 5.**

## Critical Issues

1. **P0 — Redistribution is explicitly not approved.** Root `LICENSE` is a
   placeholder and says not to redistribute. `THIRD_PARTY_NOTICES.md` says the
   institutional redistribution status of the G13/G16.1 additions is pending;
   `COLLABORATOR_HANDOFF.md` requires Wilson/Prof. Sun approval before sharing
   with Weibo. The retained stEVE and TD-MPC2 MIT notices do not resolve the
   root/institutional decision. Obtain an approved root license, attribution
   review, and explicit scope of external sharing before handoff. No legal
   conclusion is made here.
2. **P0 — The required model artifact and transfer approval are unresolved.**
   `checkpoints/` contains only `.gitkeep` and its README, intentionally no
   `step_260000.pt`. `README.md`, `checkpoints/README.md`, and
   `COLLABORATOR_HANDOFF.md` require a separately approved transfer. Without
   the exact file, a collaborator cannot reproduce the controller and this
   audit cannot verify its bytes, loading, or end-to-end behavior. Securely
   provide only the approved G13 checkpoint after transfer approval, then
   verify SHA256 `b2bba8be2e2722886c20952b15712deaa31ab612825999f1b3469a34fd6ef7be`
   and run the conditional checkpoint/inference tests. Do not commit the file.

## Important Issues

1. **P1 — Current validation is narrower than the prior release claim.**
   `tests/test_checkpoint_loading.py` skips unless `CONTACT_AWARE_CHECKPOINT`
   is set. This audit obtained 6 passes and 1 skip, not a fresh seven-test
   checkpoint run or a CUDA/SOFA demo. `docs/SHARING_AUDIT.md` records earlier
   successful checkpoint, wheel, and CUDA smoke checks; those are historical
   evidence, not independently repeated here. There is no automated
   full-controller + scene + force-extraction regression test. Rerun with the
   approved checkpoint in a clean collaborator-like environment before making
   an executable reproduction claim.
2. **P1 — SOFA/CUDA installation is not fully reproducible from the manifests.**
   `environment.yml` specifies Python 3.10 and pip only; `README.md` names
   SOFA 23.06-compatible SofaPython3/BeamAdapter and `SOFA_ROOT`/
   `SOFAPYTHON3_ROOT`, but gives no exact binary/build or plugin-install check.
   `requirements.txt` pins `torch==2.7.1`, while the README separately requires
   the CUDA 12.8 wheel `2.7.1+cu128`; package metadata alone does not enforce
   that CUDA variant. Record a tested SOFA/plugin/driver installation recipe
   and a fail-fast environment check for the intended demo platform.
3. **P1 — An older editable `eve` can shadow the bundled Generic runtime.**
   In the existing `steve_tdmpc` environment, `import eve` from this repo root
   resolved to this repo, but from `/tmp` resolved to the older research
   checkout at `/home/bizon/Desktop/stEVE/eve/__init__.py`. The three demo
   scripts prepend this repo root and `demo.run_episode()` asserts the Generic
   scene, limiting their exposure. Direct installed-package use from elsewhere
   can still select the wrong `eve` in a contaminated environment. Validate
   imports from outside the checkout in a clean environment, and document or
   guard against this collision for collaborator integrations.
4. **P1 — Physical force-adapter contract has a wiring ambiguity.**
   `interfaces/force_interface.py` defines `read_force()`, but
   `examples/phantom_integration_skeleton.py:shadow_step()` calls
   `robot.get_force()` instead and never accepts a `ForceInterface`.
   `RobotInterface` also requires `get_force()`. A team with a standalone
   proximal sensor or motor-current estimator could implement the documented
   separate interface yet not be able to use the sketch as written. Settle
   one clear dependency boundary before physical integration. No hardware
   action is currently sent by the sketch.
5. **P1 — Frozen constants are mirrored, not completely single-sourced.**
   `configs/fuzzy_safety.yaml` has `rho_0: 0.10`, while
   `safety/safety_filter.py` hardcodes `RHO_0 = 0.10`; the YAML
   `input_memberships` descriptions are not interpreted by
   `safety/fuzzy_inference.py`, which computes shapes directly from quantiles.
   `configs/simulation.yaml` also mirrors values hardcoded in force extraction
   and the SOFA scene. The current values agree, and the packaged YAML mirrors
   pass their hash test, but changing only one representation can silently
   misdescribe behavior. Add invariant checks or mark which representation is
   authoritative without altering the frozen method.

## Minor Cleanup

- **P2 — Generated local artifacts:** ignored `build/` (~1.4 MB),
  `contact_aware_tdmpc2.egg-info/` (~28 KB), `.pytest_cache/` (~32 KB), and
  many `__pycache__/` directories exist. They are not tracked and should
  remain excluded from any manual ZIP/tar handoff; do not treat the working
  directory itself as a clean release archive. No cleanup was performed.
- **P2 — Entrypoint polish:** `examples/minimal_inference.py` fails with
  `ModuleNotFoundError` when invoked from the repo root in this *uninstalled*
  environment; it works when this repo is on the import path (as it would be
  after the documented `pip install -e .`). The phantom skeleton is an
  importable sketch, not a `--help` CLI. A missing checkpoint yields a raw
  `FileNotFoundError` traceback from `tdmpc2/checkpoint.py:36` rather than a
  concise handoff instruction. Clarify example prerequisites/error wording.
- **P2 — Stale release phrasing:** `docs/SHARING_AUDIT.md` still says “before
  the proposed initial commit” and “staged” although `718a68c` exists.
  `requirements-dev.txt` includes all runtime requirements; the README uses
  it for ordinary demo installation. This is workable but heavier than needed.

## Method Identity Check

Static checks below compare implementation, frozen YAML, and documentation;
checkpoint-dependent behavior remains **unverified in this audit**. Paths are
relative to the repository root.

| Item | Expected | Actual | Status |
|---|---|---|---|
| Nominal model/planner | G13 Geometry-Force-TD-MPC2, 22-D/2-D | `tdmpc2/geometry_force.py:G13Agent`, `tdmpc2/agent.py:act`; `tdmpc2/checkpoint.py:load_g13` checks algorithm, format 2, 260000 steps, architecture/config and dimensions | Static match; checkpoint absent |
| Checkpoint | `step_260000.pt`, SHA256 `b2bba8be…fd6ef7be`; not G15 | Exact full hash in `configs/tdmpc2.yaml` and `checkpoints/README.md`; hash checked before unpickling in `load_g13()` | Config match; bytes unverified |
| Force head | Integrated `agent.model.force_head` | `tdmpc2/geometry_force.py:GeometryForceWorldModel.force_head`; loader rejects missing head | Static match |
| Observation | Exact 22-D order listed below | `env/observation.py:OBSERVATION_NAMES`; `env/g13_env.py:_augment` appends geometry eight to stEVE base fourteen | Match |
| Nominal-only prediction | Predict next force for selected nominal action, no MPPI force ranking | `controller.py:step` calls `agent.act`, then `model.force(model.next(model.encode(o), a_nom))`; `tdmpc2/agent.py` task planner has no candidate force ranking | Match |
| Current force and clearance | Previous interval `F_t`; `min(d0,d1,d2)` | `demo.py:run_episode` feeds last completed force, initialized 0; `controller.py:step` takes `min(obs[14:17])` | Match |
| Force/clearance references | Force Q75/90/95/99 = 1.0855/2.1265/3.6853/7.4666; `F_lim=3.685331040756903`; clearance Q25/50/75 = -0.6143/-0.0347/0.0842 | Full-precision values agree across `configs/fuzzy_safety.yaml` and `docs/FUZZY_SAFETY_FILTER.md`; code reads the quantiles | Match |
| Fuzzy memberships/rules | Force LOW/MEDIUM/HIGH, clearance SMALL/MEDIUM/LARGE, output NONE/MILD/STRONG, frozen R1–R10 | `safety/fuzzy_inference.py` plus `configs/fuzzy_safety.yaml`: left shoulder/triangle/right shoulder, output trapezoids/triangle, ten listed rules | Match |
| Inference | Mamdani; min AND/implication, max OR/aggregation, centroid, 0–1 grid at 0.001 | `FrozenFuzzyRisk.__init__/evaluate` checks mode/grid, takes min antecedents, min implication, max aggregation, discrete centroid over 1001 points; OR=max is declared/checked though no rule uses an OR clause | Match |
| Action filter | `rho_0=.10`; `rho_eff=0` at/below deadband else `clip((rho-.10)/.90,0,1)`; attenuate positive insertion only | `safety/safety_filter.py:effective_risk/filter_action_g161`; nonpositive insertion and rotation copied unchanged | Match; constant duplicated |
| Exclusions | No active withdrawal, G16.2 pulse, or formal CBF guarantee | No such branch in `controller.py`/`safety_filter.py`; README and `docs/METHOD.md` explicitly deny formal CBF/clinical guarantee | Match |
| Solver/contact | GenericConstraintSolver, ProjectedGaussSeidel, `1e-4`, `2000`, constraint forces true, FrictionContactConstraint `mu=.001`, `dt=.006` | `eve/intervention/simulation/sofabeamadapter.py:_basic_setup`, `env/steve_env.py` friction default, `env/scene_check.py:assert_generic_scene`, and `configs/simulation.yaml` agree | Match |
| Distal force | `||Σ J_c^T λ_c / dt||₂`, distal first ~3 mm, RL-step max across 22 substeps | `env/force_reconstruction.py:reconstruct_distal_contact_force`; `env/force_extraction.py:DistalForceMonitor.finish_step`; `env/g13_env.py:step` exposes `distal_contact_force_max_N` | Match statically; live SOFA not rerun |

`env/observation.py:OBSERVATION_NAMES` exactly matches the requested index
sequence: `p0_x,p0_y,p1_x,p1_y,p2_x,p2_y,p3_x,p3_y,p4_x,p4_y,target_x,target_y,
sin_device_rotation,cos_device_rotation,d0_normalized,d1_normalized,d2_normalized,
sin_delta_theta,cos_delta_theta,kappa_distal_normalized,r_local_normalized,
direction_valid`. `env/steve_env.py` flattens position/target/rotation in that
order. `docs/OBSERVATION_ACTION.md` gives the same order, first-12
episode-specific 2-D normalization, `tanh(mm/20)` geometry distances/radius,
angles, 1-mm sampling, 3-D vessel registration, and proxy—not exact wall
distance—semantics. Actions are float32 `[a_v,a_omega]`: insertion then
rotation, normalized to `[-1,1]`, mapped in simulation to ±50 mm/s and
±3.14 rad/s by `env/steve_env.py:_denormalize_action` and
`env/action_adapter.py:to_device_velocity`. Physical limits require a new
validated mapping. No docs/config/source contradiction was found in these
current values; the duplication risk above remains.

## Runtime Independence

No tracked source import uses the old research repository, and a tracked-file
search found no `/tmp/`, absolute `/home/`, local username, or
`stEVE_safety_head_1e1be81` dependency. `docs/SOURCE_CODE_AUDIT.md` names
**relative provenance paths** in `RL_TDMPC/`; these are documentation, not
runtime imports. The repo vendors attributed `eve/**` source and two small STL
assets. The demos explicitly insert their own root and assert the Generic
scene; prior `docs/SHARING_AUDIT.md` records a wheel/import check, but this
audit did not reinstall or rebuild. The existing environment still has the
older `eve` import collision noted in P1, so collaborators need a clean
environment or an import-origin check when using the API outside repo scripts.

## Documentation Review

`README.md` gives the method, install/demo commands, checkpoint handling,
simulation-only force caveat, and physical-use warning. `COLLABORATOR_HANDOFF.md`
identifies included/excluded material, responsible physical interfaces, and
approval gates. `docs/METHOD.md` accurately distinguishes the nominal G13
planner from the G16.1 intervention; `docs/OBSERVATION_ACTION.md` is the exact
feature/action contract; `docs/FORCE_EXTRACTION.md` gives the solver and force
formula; `docs/FUZZY_SAFETY_FILTER.md` lists all ten rules and defuzzification;
`docs/DESIGN_RATIONALE.md` motivates, but does not certify, the design;
`docs/PHYSICAL_DEPLOYMENT.md` lays out sensor and interlock work;
`docs/SHARING_AUDIT.md` is useful historical evidence but has stale tense;
`THIRD_PARTY_NOTICES.md` identifies included source and pending status.
“Fuzzy force-risk safety filter” is the predominant, accurate name. No
formal-CBF or clinical-safety overclaim was found. Missing exact SOFA/plugin
setup and the force-interface ambiguity are the substantive usability gaps.

Entrypoint check (the three scripts' `--help` worked from the root):

| Entrypoint | Purpose / inputs | Root execution and checkpoint/error handling |
|---|---|---|
| `scripts/run_nominal_demo.py` | One G13 episode; required `--checkpoint`, optional `--seed` (1000), `--device` (`cuda:0`) | Root imports work; file is hash-checked. Missing path raises raw `FileNotFoundError`; full episode not run here. |
| `scripts/run_fuzzy_safety_demo.py` | One G16.1-filtered episode; same flags | Same import/checkpoint behavior; full episode not run here. |
| `scripts/compare_nominal_vs_safety.py` | Five fixed paired smoke seeds; required checkpoint, optional device | Reuses one scene per arm, not a scientific evaluation; `--help` works, full comparison not run here. |
| `examples/minimal_inference.py` | One 22-D inference call; required checkpoint, optional device | Needs package installed/importable; direct root invocation in this uninstalled environment failed import before argument parsing. Its all-zero input is explicitly labeled nonphysical. |
| `examples/phantom_integration_skeleton.py` | Non-actuating `shadow_step(controller,robot,adapter)` sketch; no CLI flags | Needs package installed/importable; no main or checkpoint loading; cannot be treated as a runnable hardware demo. |

## Physical Integration Readiness

Weibo's team must provide a `RobotInterface` implementation for five ordered
tracked points, device rotation, target, force proxy, bounded action delivery,
and optional reset; an `ObservationAdapter.build(robot)` producing the exact
normalized 22-D vector; and a calibrated `ForceInterface.read_force()` or a
resolved equivalent force path. It also needs registered 3-D wire/vessel
centerline and radii for three signed distal clearance proxies, valid heading,
and timestamped feedback. `docs/PHYSICAL_DEPLOYMENT.md` explicitly allows a
force sensor, proximal estimate, or motor-current estimate; the abstract
protocol does not impose one sensor, but it lacks units/timestamp/quality
metadata and is not wired into the example. SOFA force reconstruction,
simulator episode normalization/geometry, ±50/±3.14 velocity mapping, and
`F_lim`/membership calibration are simulation-specific. Keep the G13 model,
22-D ordering, nominal-only prediction, ten fuzzy rules, and G16.1 action
formula frozen until separately authorized validation. The docs state 7.5-Hz
control (`22 × 0.006`-s SOFA substeps), latency alignment, and shadow-mode
logging before any actuation. The sketch does not call `send_action()`; no
watchdog, interlock, emergency stop, physical normalization, or force
calibration is implemented. Therefore it is an integration contract, **not**
a ready-to-drive physical controller.

## Dependency Review

`pyproject.toml` packages `contact_aware_tdmpc2*` and vendored `eve*`, reads
runtime dependencies from pinned `requirements.txt`, and includes YAML/STL
package data. `requirements-dev.txt` adds `pytest==7.1.2` on top of runtime
requirements. `environment.yml` is only a Python 3.10/pip scaffold; SOFA,
SofaPython3, BeamAdapter, NVIDIA driver, and matching CUDA wheel are external.
The README's wheel command is the actual CUDA selection; `torch==2.7.1` in
requirements is compatible with but does not select `+cu128`. Other strict
pins favor the tested runtime but narrow portability. No missing Python import
was observed in the limited imports/tests, but a fresh install and full demo
could not be checked here. Avoid claiming the manifests alone reproduce the
complete simulator stack.

## Test Results

In the existing `steve_tdmpc` conda environment, pytest was not installed
into that environment, so the non-mutating run supplied cached pytest 7.1.2,
pluggy, iniconfig, and py on `PYTHONPATH`, disabled bytecode/cache writes, and
ran `python -m pytest -q -rs` (equivalent test selection to `pytest -q`).
**Result: 6 passed, 1 skipped, 0 failed.** The skipped test is
`tests/test_checkpoint_loading.py` because `CONTACT_AWARE_CHECKPOINT` was not
set. Covered: action scaling; partial 22-D order/shape; fuzzy memberships,
rule output, and packaged-config mirror; deadband, positive-insertion
attenuation, nonpositive insertion, and rotation preservation. The optional
checkpoint test would check G13 22-D/2-D, `force_head`, planner sample count,
and one CPU reference action. Missing automated coverage includes the **full**
22-index ordering, direct `ContactAwareController.step()` diagnostics and
inference with a real checkpoint, live scene/force reconstruction and
one-scene lifecycle, and physical-adapter contracts/failure behavior. Historical
CUDA/demo and 7-pass claims in `docs/SHARING_AUDIT.md` were not reverified.

## Checkpoint Handling

No `.pt`/`.pth` file is tracked or present in `checkpoints/`. `.gitignore`
excludes `checkpoints/*.pt` and `checkpoints/*.pth`; the expected filename,
full SHA256, G13/format-2/260k identity, and approved external transfer are
documented. Every demo accepts `--checkpoint`; `load_g13()` checks SHA256
**before** `torch.load(..., weights_only=False)` and then checks metadata,
dimensions, force head, and frozen model/planning/training config. Because it
unpickles a full-state file, only the trusted hash-matching artifact should be
used. Hash identity itself was **not independently measured** in this audit.
The absent-file error is a raw traceback (P2). The ignore patterns apply to
direct children of `checkpoints/`; verify any future nested staging path before
committing or packaging.

## License / Third-Party Review

**BLOCKING BEFORE EXTERNAL SHARE.** `eve/**` and two STL assets are attributed
to stEVE, with a retained MIT notice in `third_party/stEVE_LICENSE`.
`contact_aware_tdmpc2/tdmpc2/agent.py` and `world_model.py` are identified as
TD-MPC2-derived, with `third_party/TD-MPC2_LICENSE`. No additional copied
component lacking an obvious notice was identified in this inspection, but
attribution completeness should be reviewed by the responsible owners.
`LICENSE` explicitly withholds redistribution pending institutional approval
for the research additions; `COLLABORATOR_HANDOFF.md` names the required
approvers. This section is an inventory and release gate, not legal advice.

## Privacy / Security Review

Tracked-text scans for email addresses, absolute home/temp paths, the named
old research checkout, common credential/key markers, and token/password
patterns found **no actual secret or machine-local path**. The only tracked
“password/access-token” hit is the negative audit statement in
`docs/SHARING_AUDIT.md:27`. `docs/SOURCE_CODE_AUDIT.md` contains relevant
relative historical source paths (`RL_TDMPC/...`) but no absolute machine
path. Ignored generated build/egg-info/pytest-cache text had no targeted
path/secret hit. Git commit metadata identifies `Bizon Tech
<bizon@example.com>` (a placeholder-looking address); Wilson should confirm
that this public-history attribution is acceptable. Public copyright names
in retained notices are third-party attribution, not detected private data.
This was a targeted text scan, not a guarantee against every possible secret
or opaque binary content.

## Git Hygiene

`git status --short` was clean before this report; branch `main`; last/five
available log entries consist of `718a68c Initial shareable contact-aware
TD-MPC2 release`. No remote is configured. `git ls-files` reports 208 files,
approximately 887,169 tracked bytes; repository working tree is about 5.8 MB
including ignored generated files, and loose Git object storage about 1.06 MB.
Largest tracked items are two `unit_sphere.stl` meshes (222,584 bytes each)
and `eve/intervention/simulation/sofabeamadapter.py` (24,525 bytes). No
historical CSV/log/video/trajectory/checkpoint, copied experiment tree,
IDE metadata, build output, egg-info, `__pycache__`, or `.pytest_cache` is
tracked. The latter generated directories are present but ignored. A Git
source checkout is cleaner than a raw directory archive; do not include
ignored artifacts in a collaborator bundle.

## Recommended Next Actions

- **P0 (2):** (1) Obtain and record institutional/collaborator approval for
  root licensing, third-party notice review, and external sharing scope;
  (2) approve a secure transfer of the exact G13 checkpoint, verify its SHA256
  on receipt, and run the checkpoint-dependent gate before handoff.
- **P1 (5):** (1) Run clean-environment checkpoint, package-import, CUDA/SOFA
  smoke and targeted controller/force tests; (2) document exact SOFA/plugin/
  CUDA installation and checks; (3) resolve `eve` import precedence outside
  repo scripts; (4) settle and test the RobotInterface/ForceInterface split;
  (5) add configuration-drift invariants while preserving frozen values.
- **P2:** Exclude ignored generated directories from archives, polish the two
  example prerequisites and missing-file error, update stale audit tense,
  and optionally separate minimal runtime from development installation.

Wilson's suggested next manual review order: `LICENSE`,
`THIRD_PARTY_NOTICES.md`, `checkpoints/README.md`,
`contact_aware_tdmpc2/controller.py`, `docs/PHYSICAL_DEPLOYMENT.md`.
