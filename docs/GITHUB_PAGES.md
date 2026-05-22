# GitHub Pages Static Visualizer

The Streamlit application remains the local research UI because it runs Python and SciPy on demand.
GitHub Pages cannot run that server-side Python process, so the public `github.io` version is a static build.

The static build performs these steps during GitHub Actions deployment:

1. Install the Python package.
2. Integrate representative two-body, restricted three-body, and general figure-eight trajectories.
3. Compute invariant drift, stability, analysis-atlas distribution, representative Jacobi escape-cone certificates, Picard contraction tuning, and hysteresis grammar Markov diagnostics with bootstrap uncertainty.
4. Embed the resulting Plotly figures, certificate bars, promotion gates, and metrics into `site/index.html`.
5. Publish the generated `site` directory through GitHub Pages.

Build locally:

```powershell
& 'D:\Codex\.venv\Scripts\python.exe' -m threebody.ui.static_site --output site
```

Open `site/index.html` in a browser to inspect the static version before deployment.

Limitations:

- It is interactive as a Plotly page, but it is not a live solver.
- Parameter sliders remain in the Streamlit app.
- The Jacobi escape-cone panel shows a representative flyby plus the latest parameter-box summary; the full theorem suite remains a local/CI research check.
- The Picard and symbolic-dynamics panel shows representative promotion gates: contraction reserve and hysteresis Markov-vs-baseline diagnostics, including the bootstrap gain interval used to avoid promoting a fragile memory effect.
- New public scenarios require adding them to `threebody.ui.static_site` and rebuilding.
