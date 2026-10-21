# Contact-Aware TD-MPC2 for Autonomous Endovascular Navigation

## Overview

Frozen G13 Geometry-Force-TD-MPC2 provides nominal guidewire navigation from
a 22-D observation. The confirmed G16.1 fuzzy force-risk safety filter monitors
current distal force, predicted force for the nominal action, and vessel-relative
clearance. It outputs a continuous intervention strength and attenuates only
positive insertion. It does not alter rotation or command withdrawal.

## Method Overview

```text
Observation → TD-MPC2 → nominal action
                         ↓
         force/geometry risk estimator
                         ↓
            Mamdani fuzzy inference
                         ↓
         deadbanded insertion attenuation → safe action
```

See [method](docs/METHOD.md), [fuzzy details](docs/FUZZY_SAFETY_FILTER.md),
and [source audit](docs/SOURCE_CODE_AUDIT.md). This is a fuzzy force-risk
safety filter, **not** a formally guaranteed control barrier function.

## Installation

On a system with an appropriate SOFA 23.06/SofaPython3/BeamAdapter installation
and NVIDIA CUDA driver, from this repository root:

```bash
conda env create -f environment.yml
conda activate contact_aware_tdmpc2
python -m pip install torch==2.7.1+cu128 --index-url https://download.pytorch.org/whl/cu128
python -m pip install -r requirements-dev.txt
python -m pip install -e .
python -c "import torch, eve, Sofa; print(torch.__version__, torch.cuda.is_available(), eve.__file__)"
```

The tested research environment was Python 3.10, PyTorch 2.7.1+cu128,
CUDA 12.8, NumPy 1.24.4, Gymnasium 0.29.1, and SOFA 23.06-compatible
SofaPython3/BeamAdapter. SOFA and its plugin paths (`SOFA_ROOT`,
`SOFAPYTHON3_ROOT`) are **system dependencies** and are not installed by pip.
The included `eve` package must resolve to this repository; the demos assert
the Generic scene before stepping. No `PYTHONPATH` to the research repository
is needed. See [force extraction](docs/FORCE_EXTRACTION.md).

## Checkpoint

Obtain the approved G13 `step_260000.pt` from the research team and verify
the SHA256 in [checkpoints/README.md](checkpoints/README.md). No checkpoint
is committed or downloaded automatically. Pass its local path explicitly.

## Run a Nominal Demo

```bash
python scripts/run_nominal_demo.py --checkpoint /path/to/step_260000.pt --seed 1000
```

## Run the Fuzzy-Safety Demo

```bash
python scripts/run_fuzzy_safety_demo.py --checkpoint /path/to/step_260000.pt --seed 1000
```

## Compare Nominal vs Safety

```bash
python scripts/compare_nominal_vs_safety.py --checkpoint /path/to/step_260000.pt
```

The five paired seeds are only a smoke/demo comparison, not a scientific
evaluation. For force inspection without a controller, run
`python scripts/inspect_force_signal.py --seed 1000`.

## Repository Structure

`contact_aware_tdmpc2/` contains the frozen controller, G13 simulation adapter,
force reconstruction, G16.1 fuzzy filter, and physical-interface contracts.
`eve/` is the attributed stEVE simulator runtime. `configs/` holds frozen
constants (mirrored as package data for wheel installs); `scripts/` and
`examples/` show usage; `tests/` checks invariants and mirror equality.
No G-series logs, training runs, or historical checkpoints are included.

## Physical Phantom Integration

Read [physical deployment](docs/PHYSICAL_DEPLOYMENT.md) and
[observation/action mapping](docs/OBSERVATION_ACTION.md). Physical sensing,
force calibration, timing, robot interlocks, and threshold selection remain
platform-specific research and validation work. The included robot adapter
is deliberately abstract and never sends hardware commands itself.

## Important Notes

`F_lim = 3.685331040756903` is a **nominal simulation statistical reference**,
not a clinical injury or safe-force threshold. The simulated distal-contact
measurement is not automatically comparable to a physical proximal sensor.
Do not use this package for patient care or autonomous physical operation
without independent validation and safety engineering.

License pending collaborator/institutional approval. **Please do not
redistribute until licensing is finalized.** See [third-party notices](THIRD_PARTY_NOTICES.md).
