# GitHub Pages Static Visualizer

The Streamlit application remains the local research UI because it runs Python and SciPy on demand.
GitHub Pages cannot run that server-side Python process, so the public `github.io` version is a static build.

The static build performs these steps during GitHub Actions deployment:

1. Install the Python package.
2. Integrate representative two-body, restricted three-body, and general figure-eight trajectories.
3. Compute invariant drift, stability, analysis-atlas distribution, representative Jacobi escape-cone certificates, Picard contraction tuning, hysteresis grammar Markov diagnostics with bootstrap uncertainty, Markov order selection, and Poincare-section word diagnostics.
4. Build a compact target-time prediction answer for the representative general three-body run, including `target_readout_decision`, `target_sensitivity_budget`, and a reproducibility certificate.
5. Embed the resulting Plotly figures, target-answer visual, fixed left section navigation, GitHub repo shortcut, certificate bars, promotion gates, progress-map timeline, compact current change ledger, public claim audit chain, and metrics into `site/index.html`.
6. Write the same machine-readable evidence bundle to `site/certificate.json`.
7. Write `site/favicon.svg` as the browser/tab icon for the public site.
8. Write `site/.gitattributes` to pin generated static artifact line endings to LF during branch publication.
9. Write `site/manifest.json` with `hash_algorithm: sha256`, SHA-256 hashes, and byte sizes for the HTML, certificate, favicon, and `.gitattributes` policy artifacts.
10. Publish the generated `site` directory through GitHub Pages.

The workflow opts JavaScript actions into the Node 24 runner path and embeds build provenance in the generated HTML
and `certificate.json`:
commit SHA, workflow run, ref name, Python version, and UTC generation time are included beside the research
certificate JSON.
`manifest.json` records SHA-256 digests so downstream checks can confirm which files belong to one generated evidence bundle, including the public browser favicon.
Run `python -m threebody.cli verify-static-artifacts --site-dir site --require-commit local --require-public-claim` to verify a local Pages artifact directory with the same public claim profile and verifier capability-set pin.
Run `python -m threebody.cli verify-static-artifacts --base-url https://eljja.github.io/3body/` to verify the public Pages bundle directly by URL.
Add `--require-commit <commit-sha-or-prefix>` when citing a specific build, so the verifier fails if GitHub Pages has moved to a different evidence bundle.
Add `--require-public-claim` to apply the versioned public claim profile and pin the running verifier's current capability-set digest in the receipt. Python callers can use `threebody_engine.public_static_artifact_claim_contract()` to inspect the profile/digest contract, then `verify_public_static_artifacts()`, `verify_public_static_artifacts_from_url()`, or `verify_public_static_artifact_bytes()` for the same public claim audit bundle through the stable engine API. `validate_public_static_artifact_receipt_contract()` checks whether the resulting receipt still matches that stable contract, and `audit_public_static_artifacts_from_url()` returns a single JSON-ready object containing the contract, receipt, validation result, and `audit_payload_sha256` report fingerprint. The profile expands to the current required promotion gates, numeric lower bounds, numeric upper bounds, and required verifier capabilities for the Pages certificate. The generated certificate and verifier receipt include the profile's canonical SHA-256 digest, and the verifier now requires the certificate's active `publication_pipeline.verification_profile`, active profile digest, and embedded canonical descriptor to agree.
The verifier also checks the static artifact identities, manifest hash algorithm, index discoverability links, publication-pipeline links, published branch line-ending policy, and the certificate's embedded verifier capability digest: `manifest.json` must identify a ThreeBody static-site manifest, declare `hash_algorithm: sha256`, `certificate.json` must identify a ThreeBody static research certificate, `index.html` must link to `certificate.json`, `manifest.json`, and `favicon.svg`, `.gitattributes` must be present in the manifest and equal `* text eol=lf`, the certificate's publication pipeline must point back to `threebody.ui.static_site`, `certificate.json`, and `manifest.json`, and the certificate's advertised verifier feature list/digest must match the verifier receipt. Receipts include both the verifier's `verification_schema_features` / `verification_schema_features_sha256` and the certificate-advertised `certificate_verification_schema_features` / `certificate_verification_schema_features_sha256`, so mismatch failures are diagnosable without reopening the certificate file. Receipts also include `receipt_payload_sha256`, a canonical SHA-256 over the receipt with `verified_at_utc` and the digest field itself excluded, so independent runs can compare the audited claim payload even though verification time differs. Callers can repeat `--require-feature <name>`, pass `--require-feature-set-sha256 <digest>`, or use `--require-current-feature-set` to pin the running verifier's current capability-set digest in the receipt. Missing or fetch-failed artifacts, missing direct byte inputs, invalid JSON, missing or non-object provenance/artifact sections, and missing commit strings are reported as failed receipt checks instead of crashing the verifier. Commit provenance only passes when both artifacts declare the same non-empty commit string.
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
- The first viewport now summarizes the original prediction target visually: deterministic `r_i(t)`, probability push-forward `Law(X_t)`, readout decision, sensitivity budget, and certificate digest.
- A fixed left navigation rail links directly to the target answer, progress map, audit chain, engine upgrades, representative figures, promotion gates, build provenance, and the GitHub repository.
- The public claim audit chain consolidates the older ladder, pipeline, and seal views into one compact section: commit-pinned build, scientific gate profile, bounded numerical drift, and active canonical profile digest.
- The current change ledger gives a compact visual summary of the latest research and audit-surface deltas: compact target answer, sensitivity budget, readout decision, and certificate validation.
- The raw certificate JSON is no longer dumped into the page body; it remains available through `certificate.json` for external review and automated verification.
- New public scenarios require adding them to `threebody.ui.static_site` and rebuilding.
