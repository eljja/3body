# Science Foundation

## Two-Body Problem

The two-body problem is solvable in closed form because it can be reduced to:

1. center-of-mass motion, and
2. relative motion in a central potential.

After that reduction, the remaining dynamics are equivalent to a one-body Kepler problem.
This gives enough structure to derive:

- conic-section orbits,
- conserved energy,
- conserved angular momentum,
- and the Laplace-Runge-Lenz vector.

## Why Three-Body Is Different

The general three-body problem does not admit the same global reduction.
All bodies interact simultaneously, so the system does not collapse into a single central-force orbit.
The consequence is that the problem is generically non-integrable.

Practically, this means:

- no global closed-form solution is expected,
- long-time dynamics can be sensitive to tiny changes in initial conditions,
- and analysis must combine numerical integration with geometric and statistical tools.

## Major Historical/Practical Approaches

### 1. Special Solutions

Researchers first studied special families of solutions, including:

- Euler collinear configurations,
- Lagrange equilateral configurations,
- periodic and choreographic solutions such as the figure-eight orbit.

These are useful because they give exact or benchmarkable structures even when the general problem remains unsolved.

### 2. Restricted Three-Body Modeling

The restricted problem simplifies the dynamics by making one body massless.
This exposes useful structures such as:

- Lagrange points,
- Jacobi constant,
- zero-velocity curves,
- and local stability regions.

This is often the right first nonlinear target for software.

### 3. Numerical Integration

Modern work relies on numerical solvers:

- adaptive high-order ODE solvers,
- symplectic or structure-aware integrators,
- regularized schemes near close encounters.

The solver is not enough by itself. Numerical results must be checked against invariants and benchmark trajectories.

### 4. Dynamical Systems Analysis

Three-body dynamics are often studied through:

- Poincare sections,
- return maps,
- Lyapunov-style sensitivity measures,
- bifurcation and stability analysis,
- invariant manifolds.

This is the main bridge between raw trajectories and interpretation.

### 5. Local Reduced Models

A realistic compact model is not global.
It must be tied to a regime such as:

- near a Lagrange point,
- inside a bounded energy range,
- or around a specific orbit family.

The right standard is not universality.
The right standard is: explicit validity region, measurable error, and preserved structure where possible.

## Project Position

This project follows:

- analytic baseline for two-body,
- analysis charts for restricted and general three-body states,
- precision-first simulation as an instrument,
- variational and transport diagnostics,
- and chart-specific compact modeling.

The intended object is an atlas, not a single formula.
An orbit segment should carry a label explaining which theory currently applies:

- two-body hierarchy,
- democratic three-body interaction,
- close encounter,
- restricted Lagrange neighborhood,
- zero-velocity gateway,
- periodic-orbit neighborhood,
- chaotic transport,
- or escape/scattering transport.

The research question becomes: how do these charts cover state space, and what laws govern transitions between them?
