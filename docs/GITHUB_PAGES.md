# GitHub Pages Static Visualizer

The Streamlit application remains the local research UI because it runs Python and SciPy on demand.
GitHub Pages cannot run that server-side Python process, so the public `github.io` version is a static build.

The static build performs these steps during GitHub Actions deployment:

1. Install the Python package.
2. Integrate representative two-body, restricted three-body, and general figure-eight trajectories.
3. Compute invariant drift, stability, analysis-atlas distribution, representative Jacobi escape-cone certificates, Picard contraction tuning, hysteresis grammar Markov diagnostics with bootstrap uncertainty, Markov order selection, and Poincare-section word diagnostics.
4. Embed the resulting Plotly figures, certificate bars, promotion gates, progress-map timeline, compact public claim audit chain, and metrics into `site/index.html`.
5. Write the same machine-readable evidence bundle to `site/certificate.json`.
6. Write `site/manifest.json` with SHA-256 hashes and byte sizes for the HTML and certificate artifacts.
7. Publish the generated `site` directory through GitHub Pages.

The workflow opts JavaScript actions into the Node 24 runner path and embeds build provenance in the generated HTML
and `certificate.json`:
commit SHA, workflow run, ref name, Python version, and UTC generation time are included beside the research
certificate JSON.
`manifest.json` records SHA-256 digests so downstream checks can confirm which files belong to one generated evidence bundle.
Run `python -m threebody.cli verify-static-artifacts --site-dir site` to verify a local or downloaded Pages artifact directory.
Run `python -m threebody.cli verify-static-artifacts --base-url https://eljja.github.io/3body/` to verify the public Pages bundle directly by URL.
Add `--require-commit <commit-sha-or-prefix>` when citing a specific build, so the verifier fails if GitHub Pages has moved to a different evidence bundle.
Add `--require-profile public-claims-v1` to apply the versioned public claim profile. It expands to the current required promotion gates, numeric lower bounds, and numeric upper bounds for the Pages certificate. The generated certificate and verifier receipt include the profile's canonical SHA-256 digest, making the profile definition itself auditable.
Repeat `--require-gate <promotion_gate_name>` to make the receipt fail unless named scientific promotion gates in `certificate.json` are exactly `true`.
Repeat `--require-min <dotted.path>=<number>` to make the receipt fail unless named certificate scalars meet declared numeric lower bounds.
Repeat `--require-max <dotted.path>=<number>` to make the receipt fail unless named certificate scalars remain below declared numeric upper bounds, such as Picard contraction or invariant drift.
Add `--output .runtime/research_runs/pages-verification-receipt.json` to preserve the verification result as a machine-readable receipt with the verifier name, UTC verification time, source, commit, and all checks.

Build locally:

```powershell
& 'D:\Codex\.venv\Scripts\python.exe' -m threebody.ui.static_site --output site
```

Open `site/index.html` in a browser to inspect the static version before deployment.

Limitations:

- It is interactive as a Plotly page, but it is not a live solver.
- Parameter sliders remain in the Streamlit app.
- The Jacobi escape-cone panel shows a representative flyby plus the latest parameter-box summary; the full theorem suite remains a local/CI research check.
- The Picard and symbolic-dynamics panel shows representative promotion gates: contraction reserve, hysteresis Markov-vs-baseline diagnostics, bootstrap gain interval, and BIC-selected memory order.
- The refined chart-word promotion gate is accompanied by a multi-coordinate Poincare sweep. The fixed hierarchy-perturbation section remains a falsification diagnostic, while the coordinate sweep searches common chart diagnostics on training phases, reports the best crossing-rich section, validates its Markov memory on a held-out binary phase against both an independent-symbol baseline and a shuffled-symbol permutation control, and reports whether nearby section quantiles and nearby atlas strides pass the same held-out memory gates.
- The research progress map summarizes the current verification path visually: Picard tuning, hysteresis grammar, Markov order, Poincare sweep, permutation control, section robustness, stride robustness, and API packaging.
- The public claim audit chain consolidates the older ladder, pipeline, and seal views into one compact section: commit-pinned build, scientific gate profile, bounded numerical drift, and canonical profile digest.
- The raw certificate JSON is no longer dumped into the page body; it remains available through `certificate.json` for external review and automated verification.
- New public scenarios require adding them to `threebody.ui.static_site` and rebuilding.
