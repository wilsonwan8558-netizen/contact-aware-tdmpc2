# Required G13 checkpoint (not tracked)

Supply the frozen `step_260000.pt` using `--checkpoint /path/to/step_260000.pt`
or to `ContactAwareController(checkpoint=...)`. The repository does **not**
contain or download this 63-MB checkpoint. Obtain it from the research team by
an approved transfer channel.

Expected SHA256:
`b2bba8be2e2722886c20952b15712deaa31ab612825999f1b3469a34fd6ef7be`

It is the G13 Geometry-Force-TD-MPC2 step-260000, format-version-2 checkpoint,
with a 22-D observation encoder and integrated `agent.model.force_head`.
It is **not** the G15 direct-force-reward checkpoint. Loading rejects a hash,
metadata, dimension, architecture, or planner-config mismatch. The full-state
file uses Python pickle; load only the trusted, hash-verified file.
