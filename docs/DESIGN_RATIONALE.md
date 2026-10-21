# Why this final design

Force is measurable in the frozen simulation and behaviorally useful, but
nearby action-conditioned force ranking is highly nonlinear and was unreliable.
The final planner therefore remains task-oriented; its force head predicts
only the selected nominal action's next force for coarse risk assessment.

One-step reactive intervention can arrive too late, while direct force-reward
optimization produced excessive conservatism in the research comparison. The
filter uses both present force and anticipatory predicted force without
retraining the navigation controller.

Overlapping fuzzy memberships absorb some prediction uncertainty and convert
coarse risk into continuous positive-insertion attenuation rather than a
binary safe/unsafe decision. The `rho=0.10` deadband prevents weak fuzzy
activation from constantly altering actions. This is an empirical design,
not a certified safety guarantee.
