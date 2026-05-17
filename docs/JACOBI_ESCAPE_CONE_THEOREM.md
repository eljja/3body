# Conditional Jacobi Escape Cone Theorem

This note records the strongest theorem candidate currently implemented in the project.
It is not a proof of the general three-body problem.
It is a local escape theorem candidate for a large hierarchical regime.

## Setting

Consider the Newtonian three-body problem with positive masses `m1`, `m2`, `m3`.
Fix a hierarchy: bodies `1` and `2` form the inner binary and body `3` is the outer body.
Let:

- `r = q2 - q1`
- `R = q3 - (m1 q1 + m2 q2) / (m1 + m2)`
- `mu_R = m3 (m1 + m2) / (m1 + m2 + m3)`
- `E_R = 0.5 mu_R |Rdot|^2 - G m3 (m1 + m2) / |R|`

The center-of-mass reduced Hamiltonian has the exact split:

```text
H - T_cm = E_r + E_R + W(r, R)
```

where `E_r` is the inner Kepler energy and `W` is the difference between the true interaction of body `3` with bodies `1,2` and the binary monopole potential.

## Theorem Candidate

Assume first that for all `t >= T`:

1. no collision occurs;
2. `|R(t)| > r_* / 2`;
3. `|r(t)| <= r_*`;
4. `|Rdot(t)| <= V_*`;
5. `d|R|/dt >= v_* > 0`;
6. the quadrupole-cancelled perturbing acceleration satisfies

```text
|a_pert(t)| <= C_Q / (|R(t)| - r_* / 2)^4.
```

If at time `T`,

```text
E_R(T) > |W(T)| + mu_R V_* C_Q / (3 v_* (|R(T)| - r_* / 2)^3),
```

then `E_R(t) > 0` for all future time allowed by the hypotheses.
Consequently the selected outer body remains in a hyperbolic-elliptic escape cone relative to the selected inner binary.

## Strengthened Self-Consistent Version

The theorem suite also checks a stronger self-consistency condition.
Let `M` be the validated lower margin after subtracting the interaction remainder, the future exchange bound, and numerical inflation.
Define:

```text
v_E = sqrt(2 M / mu_R).
```

The candidate is promoted only when:

```text
min_tail d|R|/dt > 0,
v_E > 0,
min(min_tail d|R|/dt, v_E) > v_min,
future_exchange_bound < M.
```

This does not yet remove every future-tail hypothesis.
It does remove the weakest version of the argument: the outward radial floor can no longer be an arbitrary parameter disconnected from the certified energy lower bound.

## Open Cone Version

The theorem candidate is not meant to certify only one sampled trajectory.
The current implementation therefore computes a conservative open-neighborhood radius.
Let `M` be the validated lower margin and let `L_M` be a scalar sensitivity scale built from the largest certified quantities in the margin calculation.
The implemented open-cone radius is:

```text
rho = M / (2 L_M).
```

For tail data perturbations whose scalar effect on the margin is bounded by `L_M rho`, the margin remains positive by construction.
This is not yet a sharp Fréchet derivative or interval-Lipschitz proof.
It is a concrete nonzero-radius obligation that prevents the theorem candidate from being a zero-measure numerical coincidence.

## Quadrupole Envelope Check

The implementation now directly checks the sampled Jacobi perturbing acceleration:

```text
a_pert = Rddot_actual + G (m1 + m2 + m3) R / |R|^3.
```

The declared envelope must dominate this acceleration on the certified tail:

```text
|a_pert| <= C_Q / (|R| - |r|/2)^4.
```

This is still a sampled certificate, not a formal symbolic proof of the constant.
It is nevertheless a necessary paper guardrail: the theorem candidate is rejected if the `C_Q` used in the future-tail integral does not dominate the actual perturbation on the benchmark tail.

## Parameter-Box Version

The theorem suite now requires the certificate to survive a predeclared parameter box:

```text
m3 in {0.18, 0.20, 0.22}
incoming vy in {1.55, 1.60, 1.65}
binary phase in {0.0, 0.1, 0.2}
```

Every sampled grid point must satisfy:

- positive open-cone radius;
- self-consistent radial floor;
- inflated positive margin;
- quadrupole perturbation envelope.

This is still not a continuum proof over the whole box.
It is a stronger falsification target than a single trajectory or corner-only test and is the current bridge from a point certificate toward an open parameter-regime theorem.

## Interval-Box Reserve

To move beyond grid positivity, the theorem suite computes a finite-difference Lipschitz reserve on normalized parameter cells.
For each margin value `M(i,j,k)` on the 3x3x3 grid, it estimates the maximum coordinate slopes, forms:

```text
L_box = 1.25 * ||(max |Delta_m M|, max |Delta_v M|, max |Delta_phase M|)||_2
```

and subtracts the cell reserve:

```text
M_box = min_grid M - L_box * sqrt(3)/2.
```

The interval-box candidate is accepted only if `M_box > 0`.
This is not yet a rigorous interval derivative bound, but it is the first continuum-style certificate: grid positivity alone is no longer enough.

## Proof Sketch

The Jacobi split is exact after removing center-of-mass kinetic energy.
The dipole term of the binary potential vanishes because `R` is measured from the inner binary center of mass.
The remaining perturbation is quadrupole order, so its acceleration contribution is bounded by `C_Q / (|R| - r_*/2)^4` in the declared hierarchy domain.

The outer Kepler energy changes only through the perturbing acceleration:

```text
|dE_R/dt| <= mu_R |Rdot| |a_pert|.
```

Using `|Rdot| <= V_*` and `d|R|/dt >= v_*`, integrate from `T` to infinity:

```text
Integral_T^infinity |dE_R/dt| dt
  <= mu_R V_* Integral_T^infinity C_Q / (|R| - r_*/2)^4 dt
  <= mu_R V_* C_Q / (3 v_* (|R(T)| - r_*/2)^3).
```

The stated inequality says the positive outer Kepler energy margin dominates both the instantaneous interaction remainder and all future perturbative energy exchange.
Therefore the outer two-body energy cannot cross zero under the declared hypotheses.

## What Is New Here

The individual ingredients are classical: Jacobi coordinates, hierarchy expansions, escape criteria, and perturbation bounds.
The proposed contribution is the specific certificate form:

```text
outer Kepler margin
  > interaction remainder
  + quadrupole future-tail exchange integral
  + numerical inflation
```

tied to a reproducible theorem suite and transition-atlas machinery.
The claim is intentionally narrower than general escape criteria:
it is a certifiable cone inside the hierarchical escape regime, not a universal classifier.

## Current Implementation

Implemented checks:

- `jacobi_energy_decomposition`
- `jacobi_escape_sufficient_condition`
- `jacobi_future_tail_bound`
- `jacobi_inflated_margin_certificate`
- `jacobi_self_consistent_escape_cone`
- `jacobi_open_escape_cone_certificate`
- `jacobi_quadrupole_acceleration_certificate`
- parameter-box theorem-suite benchmark over mass, incoming speed, and binary phase

The theorem suite reports:

- `jacobi_energy_split_residual`
- `jacobi_escape_sufficient_condition`
- `jacobi_future_tail_exchange_bound`
- `jacobi_quadrupole_tail_assumptions`
- `jacobi_inflated_margin_lower_bound`
- `jacobi_self_consistent_radial_floor`
- `jacobi_open_cone_radius`
- `jacobi_quadrupole_acceleration_envelope`
- `jacobi_parameter_box_open_regime`
- `jacobi_parameter_box_quadrupole_ratio`
- `jacobi_parameter_grid_margin`
- `jacobi_parameter_interval_box_margin`

## Remaining Proof Obligations

- Replace sampled floating trajectories with interval-enclosed trajectories.
- Replace the finite-difference parameter-box reserve with a rigorous interval derivative bound over mass, velocity, phase, and tail state.
- Prove the declared `C_Q` bound sharply for planar and spatial dimensions.
- Replace the scalar open-cone sensitivity with an interval or automatic-differentiation Lipschitz bound.
- Replace the remaining tail extrema assumptions with invariant inequalities that propagate for all future time.
- Compare the accepted cone directly against Marchal/Standish/Szebehely-Zare style criteria on the same benchmark family.
