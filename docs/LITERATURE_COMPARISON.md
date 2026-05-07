# Literature Comparison

This project must be compared against known three-body results before making any breakthrough claim.

## Established Results We Must Not Repackage

- Sundman, 1912: convergent series representation for the three-body problem after regularization, but not a practical closed-form solution.
- McGehee, 1974: triple-collision blow-up and collision manifold analysis in the collinear three-body problem.
- Chenciner and Montgomery, 2000: variational proof of the equal-mass figure-eight orbit.
- Simó / Galán et al., 2002: numerical and continuation studies of figure-eight stability and bifurcation structure.
- CR3BP transport literature: Lagrange neck transport is commonly analyzed through invariant manifold tubes and periodic-orbit monodromy.

## Current Novelty Target

The current novelty target is not a new closed-form solution.
The target is a reproducible `Reduced Shape-Scattering Atlas`:

- one shared reduced state object,
- chart-specific local diagnostics,
- transition/scattering maps,
- held-out and artifact validation,
- and proof obligations that explicitly block overclaiming.

The only current breakthrough candidate is narrow:

```text
In a declared hierarchical flyby family, trajectory-measured scattering coordinates
can improve low hierarchy-exit boundary prediction over instantaneous geometry.
```

This is a conjecture, not a theorem.
The current `theorem-suite` fails to reproduce this candidate under the stricter paper harness, so it is not yet a breakthrough claim.
The more robust current target is therefore weaker but cleaner:

```text
instantaneous hierarchy thresholds are insufficient;
the surviving explanatory class is accumulated impulse/exchange over the encounter.
```

## What Would Count As A Real Breakthrough

- A theorem-level error bound for the hierarchy-exit scattering map in a stated mass/energy/impact regime.
- A regularized collision chart that proves smooth continuation or classifies exchange outcomes in a stated near-collision regime.
- A Lagrange gateway theorem that replaces the current linear projection with validated manifold-tube transit/non-transit classification.
- A public benchmark set where outside researchers can reproduce the atlas labels, transition laws, and failure cases.

## Current Reproducibility Command

```powershell
threebody theorem-suite
```

This emits:

- theorem candidates,
- proof obligations,
- benchmark pass/fail rows,
- and blockers preventing false claims.
