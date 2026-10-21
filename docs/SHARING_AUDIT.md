# Pre-share audit

This is a local-review package, not an approved public release.

Checks performed before the proposed initial commit:

- Frozen checkpoint SHA256 matched the expected G13 step-260000 hash. Its
  metadata reported format version 2, algorithm `Geometry-Force-TD-MPC2`,
  260,000 environment steps, 22 observation dimensions, 2 action dimensions,
  and an integrated `force_head`.
- The copied inference matched original-source CPU nominal actions and
  predicted force exactly on two seeded planner calls (maximum absolute
  difference 0). The copied fuzzy logic matched 100 sampled original-source
  risk/action evaluations exactly (maximum absolute difference 0).
- Clean-root imports resolved `eve` inside this repository, not the older
  editable stEVE package installed in the test environment. The two demo
  scripts asserted the Generic scene and completed one CUDA smoke episode each.
  Seed 1000 nominal: success, 59 steps, peak force 7.6733 nominal N. Seed
  1000 fuzzy: success, 77 steps, peak force 6.6854 nominal N, modified-action
  fraction 0.8831. These are smoke tests, not performance estimates.
- `pytest` with the trusted checkpoint supplied passed 7 tests. Both demo
  scripts' `--help` commands passed. A wheel built and was installed into a
  temporary target; from outside the source checkout it imported its own
  `eve` package and packaged YAML, and loaded the verified checkpoint.
- A targeted recursive text scan found no home-directory paths, temporary
  research-project paths, email addresses, private-key markers, API keys,
  password literals, or access-token literals.
- The file/size scan found no copied checkpoint, experiment CSV, large log,
  temporary rollout, video, or source file over 5 MB. Generated caches are
  excluded by `.gitignore` and are not committed. The release stages 208 files:
  143 attributed stEVE runtime files (141 Python sources, 2 small mesh assets)
  and 65 controller/config/documentation/test/notice files. The largest
  staged file is a 223-kB mesh asset.
- Third-party source notices are preserved under `third_party/` and explained
  in `THIRD_PARTY_NOTICES.md`. The root license is intentionally pending
  institutional approval; **redistribution remains blocked** until approved.

The exact test commands/results and tracked-file audit should be checked again
after packaging and before any collaborator transfer. Git history is local;
no remote or external upload is authorized.
