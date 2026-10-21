# Frozen G16.1 fuzzy force-risk filter

Inputs are current distal force `F_t`, nominal-action predicted next force
`F_hat_next`, and `d_wall=min(d0,d1,d2)`. Force units are nominal simulation N;
clearance is normalized and signed. Exact breakpoints are in
[`configs/fuzzy_safety.yaml`](../configs/fuzzy_safety.yaml).

For a left shoulder `L(x;a,b)=clip((b-x)/(b-a),0,1)`, triangle
`T(x;a,b,c)=max(0,min((x-a)/(b-a),(c-x)/(c-b)))`, and right shoulder
`R(x;a,b)=clip((x-a)/(b-a),0,1)`:

| Input | Membership | Shape and breakpoints |
|---|---|---|
| current and predicted force | LOW | `L(F;Q75,Q90)` |
| current and predicted force | MEDIUM | `T(F;Q75,Q95,Q99)` |
| current and predicted force | HIGH | `R(F;Q90,Q95)` |
| clearance | SMALL | `L(d;Q25,Q50)` |
| clearance | MEDIUM | `T(d;Q25,Q50,Q75)` |
| clearance | LARGE | `R(d;Q50,Q75)` |

Force quantiles: Q75 `1.0855235286650953`, Q90 `2.1265156799878246`,
Q95 `3.685331040756903`, Q99 `7.466568793559142`. Clearance quantiles:
Q25 `-0.6142929047346115`, Q50 `-0.03466621972620487`, Q75
`0.08420414663851261`.

Output memberships on `rho∈[0,1]` at `0.001` intervals are NONE trapezoid
`[0,0,0.1,0.25]`, MILD triangle `[0.1,0.4,0.7]`, and STRONG trapezoid
`[0.55,0.75,1,1]`.

| Rule | Antecedents (AND) | Output |
|---|---|---|
| R1 | current LOW, predicted LOW, clearance LARGE | NONE |
| R2 | current LOW, predicted LOW, clearance MEDIUM | MILD |
| R3 | predicted MEDIUM | MILD |
| R4 | current MEDIUM, predicted LOW | MILD |
| R5 | predicted HIGH | STRONG |
| R6 | current HIGH | STRONG |
| R7 | current MEDIUM, predicted MEDIUM | STRONG |
| R8 | clearance SMALL, predicted MEDIUM | STRONG |
| R9 | clearance SMALL, predicted HIGH | STRONG |
| R10 | clearance SMALL, current LOW, predicted LOW | MILD |

Mamdani inference uses AND=`min`, OR=`max`, implication=`min`, aggregation=
`max`, and centroid defuzzification. For each rule `i`, let strength `s_i`
be the minimum antecedent membership; aggregate
`mu(r)=max_i min(s_i,mu_consequent_i(r))`. Then
`rho=sum_r r*mu(r)/sum_r mu(r)` on the 1001-point grid.

The final deadband is `rho_0=0.10`:

```text
rho_eff = 0                              if rho <= 0.10
rho_eff = clip((rho-0.10)/0.90,0,1)      otherwise
a_v_safe = (1-rho_eff)*a_v_nom           if a_v_nom > 0
a_v_safe = a_v_nom                       otherwise
a_omega_safe = a_omega_nom
```

Precise nearby-action counterfactual force ranking was unreliable; coarse
anticipatory risk was informative. Overlapping memberships convert that risk
into continuous insertion attenuation without a brittle binary decision.
There is no active withdrawal, rotation modification, or formal CBF guarantee.
