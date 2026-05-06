# Solution Space

The project should not collapse into one proposed mechanism too early.
The current flyby work is only one chart family: a tight binary perturbed by an outer body.
Below are the major solution directions that can still matter for a regime-specific three-body theory.

## What The Current Two Axes Can Miss

The current strongest axes are accumulated tidal impulse and inner-binary exchange.
They can miss at least four mechanisms:

- Phase dependence: identical encounter strength can produce different outcomes depending on the binary phase at closest approach.
- Resonant exposure: slow encounters can repeatedly sample the inner orbit rather than acting as a single kick.
- Manifold routing: escape and temporary capture can be governed by stable/unstable manifolds rather than a local threshold.
- Collision geometry: close approaches can require regularized coordinates because ordinary Euclidean features become singular or misleading.

## Candidate Solution Families

- Phase-resolved scattering map: fit transition and exchange laws conditioned on binary phase, encounter duration, and tidal impulse.
- Manifold atlas: identify chart transitions as motion between hierarchy, resonant, collision, and escape manifolds.
- Shape-sphere dynamics: remove translation, rotation, and scale where possible, then analyze the remaining triangle-shape flow.
- Regularized collision charts: use Levi-Civita, Kustaanheimo-Stiefel style ideas, or local blow-up coordinates near binary collisions.
- Normal-form neighborhoods: near Lagrange points, periodic orbits, and weakly perturbed binaries, derive local analytic approximations.
- Scattering and return maps: treat flybys as maps from incoming orbital elements to outgoing orbital elements, then compose maps.
- Symbolic dynamics: encode regime changes as grammar over chart labels and test whether transition words have stable probabilities.
- Variational stability: use tangent dynamics, finite-time Lyapunov exponents, and monodromy/Floquet data where periodic orbits exist.
- Invariant-preserving surrogates: learn only residual corrections that preserve energy, momentum, angular momentum, or Jacobi structure.

## Near-Term Research Priority

The immediate priority is the phase-resolved scattering map because it directly targets the current residual cluster.
The required evidence is a held-out phase sweep:

```powershell
threebody flyby-sweep --heldout --phase-sweep --duration 8 --samples 600 --stride 20
```

If phase-conditioned models win, the compact model should be a local scattering map:

```text
boundary ~= F(tidal_impulse, exchange, encounter_adiabaticity, hierarchy_ratio, binary_phase_at_encounter)
```

If they fail, the project should pivot to manifold routing and regularized close-encounter coordinates for the same residual cases.

The current implementation measures `binary_phase_at_periapsis` from the trajectory rather than relying only on initial phase.
That is necessary but not sufficient.
A real scattering map must predict outgoing energy, angular momentum, deflection angle, and chart transition probability jointly, not just reuse phase as another multiplicative power-law feature.
The first smoke result is encouraging only for low-crossing boundary collapse; high-crossing selection still prefers a simpler impulse model after complexity penalty.

Current atlas additions:

- Close/triple collision: `mcgehee_collision_diagnostic` separates hyperradius, radial velocity, normalized shape area, anisotropy, and collision depth.
- Escape/flyby scattering: `periapsis_scattering_map` now reports outgoing semimajor axis, eccentricity, periapsis distance, and escape speed at infinity.
- Lagrange gateway: `gateway_transit_estimate` tests whether the local neck is open and projects the state onto stable/unstable eigendirections around the nearest collinear point.
