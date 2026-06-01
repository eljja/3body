# Conditional Jacobi Escape Cone Theorem

This note records the strongest theorem candidate currently implemented in the project.
It is not a proof of the general three-body problem.
It is a local escape theorem candidate for a declared hierarchical benchmark
regime, with open proof obligations before any journal-level computer-assisted
proof claim.

Korean summary: 이 문서는 일반 삼체 문제의 증명이 아니라, 계층적 escape
tail에서 성립할 수 있는 조건부 정리 후보를 기록한다. 현재 구현은 sampled
trajectory, interval tail box, segment-wise Picard guardrail을 결합하지만,
독립 validated ODE backend와 interval parameter derivative bound가 완성되기
전까지는 논문에서 "완성된 컴퓨터 보조 증명"으로 표현하면 안 된다.

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

The paper-mode theorem suite now requires the certificate to survive a predeclared parameter box:

```text
m3 in {0.18, 0.20, 0.22}
incoming vy in {1.60, 1.625, 1.65}
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

## Interval Tail-State Box

The implementation now adds a stricter local interval certificate over the sampled outgoing tail.
For each tail sample, the state is replaced by a nonzero interval box:

```text
y_i in [y_i - rho, y_i + rho],
rho = absolute_state_radius + relative_state_radius * ||tail||_inf.
```

On that box, the code interval-encloses:

- the outer Kepler energy `E_R`;
- the true interaction remainder `W`;
- the radial velocity `d|R|/dt`;
- the hierarchy ratio `|R| / |r|`;
- the terminal outer radius, maximum binary scale, outer speed, and quadrupole acceleration constant used in the future-tail exchange integral.

The interval certificate accepts only if:

```text
inf_tail E_R - sup_tail |W| - sup future_exchange_bound > 0
```

and the interval radial floor, hierarchy ratio, and denominator radius remain inside the declared theorem domain.
This replaces the previous scalar-only margin guardrail for the local tail data.
It still does not prove that the numerical integrator enclosed the true ODE solution over the entire trajectory.
That remaining step requires interval ODE integration or an equivalent a posteriori validated flow enclosure.

## A Posteriori Interval Flow Tube

The theorem suite now adds a first flow-level guardrail for the outgoing tail.
For each sampled tail segment `[t_k, t_{k+1}]`, the code computes the trapezoid defect:

```text
d_k = y_{k+1} - y_k - 0.5 * dt * (f(y_k) + f(y_{k+1})).
```

It then expands the componentwise segment hull by:

```text
rho_flow = defect_safety_factor * max_k ||d_k||_inf
```

and interval-evaluates the Newtonian RHS on that expanded hull.
The flow-tube certificate requires:

- every sampled segment slope `(y_{k+1} - y_k) / dt` lies inside the interval RHS box for that segment;
- the Jacobi interval escape margin remains positive when the tail-state box radius is set to `rho_flow`.

This is not yet a full interval ODE solver because it does not construct a contraction proof or propagate interval initial data through the whole integration interval.
It is nevertheless stronger than an isolated tail-state interval check: the accepted escape margin now survives a tube whose radius is chosen from the measured local integration defect and whose vector field is interval-enclosed segment by segment.

## Segment-Wise Interval Picard Propagation

The next proof guardrail propagates interval boxes instead of only checking sampled slopes.
Each tail segment is subdivided until an interval Newtonian RHS Jacobian row-sum bound gives a contraction factor below one.
For each substep, the code checks Picard self-inclusion:

```text
X_start + h_sub f(Z) subset Z
```

where `X_start` is the propagated interval start box and `Z` is the expanded sampled subsegment hull.
The propagated final box for each sampled segment must also intersect the endpoint tube.
The maximum radius needed to cover these propagated endpoint boxes is then used as the absolute tail-state radius in the final Jacobi interval escape check.

This is the first in-repository validated-flow step.
It is still not a CAPD-grade integrator: the interval Jacobian bound is deliberately conservative, the tube is built around a sampled trajectory, and the theorem-suite parameter box currently uses a fixed finite grid rather than interval parameters.
But it does cross the previous bottleneck: an interval initial box is now propagated through the outgoing Jacobi tail by a contraction-style Picard inclusion check.

## Picard-Certified Parameter Reserve

The paper-mode parameter-box continuum reserve is now also computed from the Picard-certified tail margin.
For the predeclared grid in `(m3, incoming vy, binary phase)`, the theorem suite forms a normalized finite-difference Lipschitz reserve using:

```text
M_picard = Picard-certified interval tail escape margin.
```

The accepted cell lower bound is:

```text
M_picard_box = min_grid M_picard - L_picard * sqrt(3)/2.
```

This still is not a true interval-parameter derivative proof, because the derivative is estimated from the finite grid.
It does close an important loophole: the continuum-style parameter reserve is no longer based only on scalar-inflated margins, but on the same margin that survived interval Picard propagation.

The suite also evaluates the midpoint of every parameter cell.
Each midpoint must pass the Picard-certified Jacobi escape check, and the midpoint margin must stay positive after subtracting the observed center-to-corner variation inside the cell.
The suite additionally evaluates every parameter-cell face center.
Each face center must pass Picard-certified Jacobi escape, and its margin must stay positive after subtracting the observed face-center-to-corner variation on that face.
The suite also evaluates every parameter-cell edge center.
Each edge center must pass Picard-certified Jacobi escape, and its margin must stay positive after subtracting the observed edge-center-to-corner variation on that edge.
Together these checks cover the full 5x5x5 half-grid induced by the original 3x3x3 parameter grid.
The same half-grid is also used to compute a smaller-subcell continuum-style reserve:

```text
M_half_grid = min_half_grid M_picard - L_half_grid * sqrt(3)/4.
```

In paper mode, the suite also computes local reserves for each of the 64 smaller subcells, using only the eight Picard-certified corners of that subcell.
The reported lower bound is the minimum of these local subcell reserves.

This does not replace an interval-parameter derivative bound, but it rules out the simplest failure modes where all grid points pass while cell centers, face interiors, edge interiors, or half-grid subcells immediately collapse.

## Resolution/Tolerance Crosscheck

The representative Jacobi tail is now re-integrated under a predeclared sweep of sample counts and adaptive tolerances:

```text
(samples, rtol, atol) in {
  (500, 1e-9,  1e-11),
  (520, 1e-9,  1e-11),
  (500, 1e-10, 1e-12),
  (500, 1e-8,  1e-10)
}
```

Each re-integrated trajectory must pass the same segment-wise interval Picard flow certificate, with the Picard-propagated endpoint radius fed back into the Jacobi interval margin.
The theorem suite reports both the minimum Picard-certified escape margin and the maximum margin spread across this sweep.
This is still not an independent validated integrator, but it blocks a weaker failure mode: the accepted cone cannot be only an artifact of one `samples/rtol/atol` choice.

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
- `jacobi_interval_escape_certificate`
- `jacobi_interval_flow_tube_certificate`
- `jacobi_interval_picard_flow_certificate`
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
- `jacobi_interval_tail_escape_margin`
- `jacobi_interval_flow_tube`
- `jacobi_interval_picard_flow`
- `jacobi_picard_interval_jacobian_contraction`
- `jacobi_picard_resolution_crosscheck`
- `jacobi_picard_resolution_margin_spread`
- `jacobi_quadrupole_acceleration_envelope`
- `jacobi_parameter_box_open_regime`
- `jacobi_parameter_box_quadrupole_ratio`
- `jacobi_parameter_grid_margin`
- `jacobi_parameter_interval_box_margin`
- `jacobi_parameter_interval_tail_margin`
- `jacobi_parameter_flow_tube_margin`
- `jacobi_parameter_picard_flow_margin`
- `jacobi_parameter_picard_interval_box_margin`
- `jacobi_parameter_picard_cell_centers`
- `jacobi_parameter_picard_face_centers`
- `jacobi_parameter_picard_edge_centers`
- `jacobi_parameter_picard_half_grid_margin`
- `jacobi_parameter_picard_half_grid_subcells`

## Remaining Proof Obligations

- Replace the segment-wise Picard flow check with a production-grade interval ODE integrator or independently verified CAPD/Arb-style implementation.
- Replace the Picard-margin finite-difference parameter-box reserve with a rigorous interval derivative bound over mass, velocity, phase, and tail state.
- Replace the current resolution/tolerance crosscheck with an independent validated integration backend, so solver dependence is controlled by proof rather than by a finite reproducibility sweep.
- Prove the declared `C_Q` bound sharply for planar and spatial dimensions.
- Replace the scalar open-cone sensitivity with an interval or automatic-differentiation Lipschitz bound.
- Replace the remaining tail extrema assumptions with invariant inequalities that propagate for all future time.
- Compare the accepted cone directly against Marchal/Standish/Szebehely-Zare style criteria on the same benchmark family.
