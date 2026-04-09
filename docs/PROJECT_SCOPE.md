# Project Scope

## Purpose

This project studies the two-body and three-body problems through code, with emphasis on:

- high-precision numerical integration,
- invariant tracking,
- phase-space interpretation,
- interactive visualization,
- and regime-specific compact modeling.

The project does not claim a universal closed-form solution of the general three-body problem.

## Why This Exists

The two-body problem is analytically tractable after reduction to a central-force problem.
The three-body problem is not generically integrable in the same way, so a practical research workflow must combine:

- trusted numerical solvers,
- physical diagnostics,
- structured benchmark orbits,
- and local reduced models with explicit validity limits.

## Current Deliverables

- reusable Python package under `src/threebody`
- analytic and numerical solvers
- diagnostics for conserved quantities and sensitivity
- reference orbit scenarios
- Streamlit visualizer
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
