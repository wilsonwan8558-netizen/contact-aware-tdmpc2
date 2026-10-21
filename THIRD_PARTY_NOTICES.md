# Third-party notices

`eve/**` is the stEVE simulation runtime copied from the research source at
commit `540fca2aae99c1e6bc30102a20a3fa0973ac95ea`. It is covered by the
research source root MIT notice, preserved verbatim in
`third_party/stEVE_LICENSE` (copyright Lennart Karstensen, 2023). The
Generic-SOFA scene settings in its `sofabeamadapter.py` are essential to this
release's simulation behavior. The runtime source and its two tracked `.stl`
assets are included; the research experiment tree is not.

`contact_aware_tdmpc2/tdmpc2/agent.py` and `world_model.py` are adapted from
the project's compact TD-MPC2 integration, itself based on the official
[TD-MPC2](https://github.com/nicklashansen/tdmpc2) implementation at commit
`e9f5932`. Its MIT notice is preserved verbatim in
`third_party/TD-MPC2_LICENSE` (copyright Nicklas Hansen, 2023).

The G13 geometry/force additions and G16.1 fuzzy filter were adapted from
the research worktree. Their institutional redistribution status remains to
be approved; the root `LICENSE` is therefore a placeholder, not a grant.
