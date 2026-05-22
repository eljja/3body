# GitHub Pages Static Visualizer

The Streamlit application remains the local research UI because it runs Python and SciPy on demand.
GitHub Pages cannot run that server-side Python process, so the public `github.io` version is a static build.

The static build performs these steps during GitHub Actions deployment:

1. Install the Python package.
2. Integrate representative two-body, restricted three-body, and general figure-eight trajectories.
3. Compute invariant drift, stability, analysis-atlas distribution, representative Jacobi escape-cone certificates, Picard contraction tuning, hysteresis grammar Markov diagnostics with bootstrap uncertainty, Markov order selection, and Poincare-section word diagnostics.
4. Embed the resulting Plotly figures, certificate bars, promotion gates, progress-map timeline, and metrics into `site/index.html`.
5. Write the same machine-readable evidence bundle to `site/certificate.json`.
6. Publish the generated `site` directory through GitHub Pages.

The workflow opts JavaScript actions into the Node 24 runner path and embeds build provenance in the generated HTML
and `certificate.json`:
commit SHA, workflow run, ref name, Python version, and UTC generation time are included beside the research
certificate JSON.

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
- New public scenarios require adding them to `threebody.ui.static_site` and rebuilding.
