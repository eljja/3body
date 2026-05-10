# GitHub Pages Static Visualizer

The Streamlit application remains the local research UI because it runs Python and SciPy on demand.
GitHub Pages cannot run that server-side Python process, so the public `github.io` version is a static build.

The static build performs these steps during GitHub Actions deployment:

1. Install the Python package.
2. Integrate representative two-body, restricted three-body, and general figure-eight trajectories.
3. Compute invariant drift, stability, analysis-atlas distribution, and theorem-suite summary values.
4. Embed the resulting Plotly figures and metrics into `site/index.html`.
5. Publish the generated `site` directory through GitHub Pages.

Build locally:

```powershell
& 'D:\Codex\.venv\Scripts\python.exe' -m threebody.ui.static_site --output site
```

Open `site/index.html` in a browser to inspect the static version before deployment.

Limitations:

- It is interactive as a Plotly page, but it is not a live solver.
- Parameter sliders remain in the Streamlit app.
- New public scenarios require adding them to `threebody.ui.static_site` and rebuilding.
