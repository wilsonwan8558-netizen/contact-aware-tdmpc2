# Frozen contact-aware method

The G13 controller chooses *where* to navigate. The G16.1 fuzzy filter chooses
how aggressively positive insertion should be applied. Both are frozen;
there is no G16.2 withdrawal, MPPI force reranking, or force-reward training.

For the 22-D G13 observation `o_t`, the nominal model/planner uses

```text
z_t                 = E(o_t)
a_nom               = TD-MPC2_MPPI(o_t)  [implemented by agent.act]
z_hat_(t+1)         = f(z_t, a_nom)
F_hat_(t+1)         = g_F(z_hat_(t+1))
d_wall              = min(o_t[14], o_t[15], o_t[16])
rho                 = F_fuzzy(F_t, F_hat_(t+1), d_wall)
rho_eff             = 0                         if rho <= 0.10
                    = clip((rho-0.10)/0.90,0,1)  otherwise
a_v_safe            = (1-rho_eff) a_v_nom        if a_v_nom > 0
                    = a_v_nom                    otherwise
a_omega_safe        = a_omega_nom
```

Here `F_t` is the previous completed RL interval's measured distal-contact
force, initialized to zero at episode start. The force predictor is the
`force_head` inside the **same** G13 checkpoint as the planner. The force
prediction is evaluated only for the selected nominal action, not used to
rank MPPI candidates. `d_wall` is a signed centerline-radius proxy, not an
exact collision-mesh distance.

The planner's latent rollouts, policy-action mix, elite weighting, warm start,
and deterministic evaluation action are unchanged from G13. Call
`ContactAwareController.reset_episode()` for each new episode so the planner
warm-start lifecycle matches the original. Pass a finite 22-D observation
and finite nonnegative current force to `step()`. The returned action is
normalized `[a_v,a_omega]`; diagnostics contain nominal action, predicted
force, clearance, memberships, rule strengths, `rho`, `rho_eff`, and safe action.

This is a fuzzy force-risk safety filter (or fuzzy CBF-style minimum-
intervention filter), **not a formally guaranteed CBF**. Neither the learned
force predictor nor the proxy clearance provides a certified barrier.
