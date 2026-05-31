# Project Scope

## Purpose

This project tries to build an analysis method for the three-body problem through code.
The visualizer exists only to support intuition while developing that method.

The working objective is an analysis atlas:

- classify each state into an interpretive chart,
- apply the best known method inside that chart,
- detect transitions between charts,
- preserve or measure the drift of relevant invariants,
- and construct local compact models with explicit validity conditions.

The project does not claim a single universal closed-form solution of the general three-body problem.
It aims to make the problem analyzable by decomposing it into connected local descriptions.
For paper-facing language, the project distinguishes operational numerical
answers, reproducibility certificates, theorem candidates, and completed
computer-assisted proofs as separate claim levels.

## Why This Exists

The two-body problem is analytically tractable after reduction to a central-force problem.
The three-body problem is not generically integrable in the same way, so the project should combine:

- trusted numerical solvers as measurement devices,
- invariant and variational diagnostics,
- chart-specific classical methods,
- transition maps between charts,
- and structure-aware model discovery.

## Current Deliverables

- reusable Python package under `src/threebody`
- analytic and numerical solvers
- diagnostics for conserved quantities and sensitivity
- first-pass analysis atlas and chart classifier
- finite-difference local linearization tools
- perturbation ensembles, transition surveys, and first-pass law mining
- reference orbit scenarios
- Streamlit visualizer
- static GitHub Pages evidence bundle with machine-readable verification artifacts
- finite-time prediction API for target positions and pushed-forward probability distributions
- automated tests

## Boundaries

Included now:

- nondimensional Newtonian gravity
- planar restricted three-body problem
- planar equal-mass figure-eight benchmark
- polynomial local compact model fitting

Not included yet:

- relativistic corrections
- full collision regularization
- manifold continuation workflows
- production-scale parameter sweeps
- universal surrogate modeling
