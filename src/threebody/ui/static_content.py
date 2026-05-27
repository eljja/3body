from __future__ import annotations

from dataclasses import dataclass
import html


GITHUB_REPO_URL = "https://github.com/eljja/3body"


@dataclass(frozen=True)
class MenuItem:
    panel_id: str
    label: str
    short_label: str


@dataclass(frozen=True)
class ContentPanel:
    panel_id: str
    title: str
    lead: str
    equation: str
    bullets: tuple[str, ...]
    status: str


FLOATING_MENU_ITEMS: tuple[MenuItem, ...] = (
    MenuItem("threebody-answer", "Three-body answer", "3B"),
    MenuItem("riemann-hypothesis", "Riemann Hypothesis", "RH"),
    MenuItem("collatz-conjecture", "Collatz Conjecture", "C"),
    MenuItem("goldbach-conjecture", "Goldbach Conjecture", "G"),
    MenuItem("twin-prime", "Twin Prime Workbench", "TP"),
    MenuItem("progress-map", "Progress", "P"),
    MenuItem("public-audit", "Audit", "A"),
    MenuItem("build-provenance", "Build", "B"),
)


CONTENT_PANELS: tuple[ContentPanel, ...] = (
    ContentPanel(
        panel_id="threebody-answer",
        title="Three-body target answer",
        lead=(
            "The current engine answers the original finite-time question: compute deterministic "
            "positions when the flow remains resolved, otherwise report the pushed-forward target "
            "distribution under the declared initial uncertainty."
        ),
        equation="r_i(t) = Pi_{r_i} Phi_t(x(0));  Law(X_t) = (Phi_t)# Law(X_0)",
        bullets=(
            "Compact answer: target positions, probability regions, pair geometry, and center-of-mass readout.",
            "Decision gate: target_readout_decision chooses point positions, probability regions, deterministic-only, or unresolved.",
            "Predictability budget: target_sensitivity_budget ties the answer to horizon, tolerance, FTLE, and close-approach diagnostics.",
        ),
        status="implemented",
    ),
    ContentPanel(
        panel_id="riemann-hypothesis",
        title="Riemann Hypothesis",
        lead=(
            "This panel is a future research slot, not a claimed proof. It frames the hypothesis as "
            "a reproducible verification workflow: statements, equivalent criteria, computed evidence, "
            "and explicit failure modes."
        ),
        equation="zeta(s)=0, 0 < Re(s) < 1  =>  Re(s)=1/2",
        bullets=(
            "Track equivalent formulations separately from numerical zero checks.",
            "Require interval or certified arithmetic before promoting any computational statement.",
            "Keep every claim scoped: finite verification evidence is not a proof of the full theorem.",
        ),
        status="research-outline",
    ),
    ContentPanel(
        panel_id="collatz-conjecture",
        title="Collatz Conjecture",
        lead=(
            "This panel organizes Collatz exploration as symbolic dynamics and descent certificates. "
            "It deliberately separates exhaustive finite checks from any global termination claim."
        ),
        equation="T(n)=n/2 if n even;  T(n)=3n+1 if n odd",
        bullets=(
            "Use residue-class transition graphs to expose memory and drift structure.",
            "Record stopping-time distributions and counterexample search bounds as auditable artifacts.",
            "Only promote local descent certificates when every branch in the declared box is covered.",
        ),
        status="research-outline",
    ),
    ContentPanel(
        panel_id="goldbach-conjecture",
        title="Goldbach Conjecture",
        lead=(
            "This panel treats Goldbach as a certificate search problem: each even integer is paired "
            "with a verifiable prime decomposition, while asymptotic arguments stay clearly separated."
        ),
        equation="For every even N > 2,  N = p + q with p,q prime",
        bullets=(
            "Expose witness pairs and primality certificates instead of only counts.",
            "Separate finite range verification from analytic density estimates.",
            "Use hashed witness tables when publishing large computational ranges.",
        ),
        status="research-outline",
    ),
    ContentPanel(
        panel_id="twin-prime",
        title="Twin Prime Workbench",
        lead=(
            "This panel is a future interface for bounded-gap prime evidence and admissible tuple "
            "experiments. It does not assert the twin prime conjecture."
        ),
        equation="infinitely many p such that p and p+2 are prime",
        bullets=(
            "Keep bounded-gap theorems, sieve experiments, and direct twin-prime witnesses in separate tracks.",
            "Attach primality certificates and search-range digests to published witness data.",
            "State which claims are heuristic, computational, or theorem-backed.",
        ),
        status="research-outline",
    ),
)


def render_floating_nav() -> str:
    buttons = "\n".join(
        (
            '<button type="button" class="nav-panel-button" '
            f'data-panel-target="{html.escape(item.panel_id)}" '
            f'data-short="{html.escape(item.short_label)}">'
            f"{html.escape(item.label)}</button>"
        )
        for item in FLOATING_MENU_ITEMS
    )
    return (
        '<nav class="floating-nav" aria-label="Content panel navigation">'
        f"{buttons}"
        f'<a class="repo-link" href="{html.escape(GITHUB_REPO_URL)}" data-short="GH" '
        'target="_blank" rel="noopener noreferrer">GitHub repo</a>'
        "</nav>"
    )


def render_content_workspace() -> str:
    panels = "\n".join(
        _render_content_panel(panel, active=(index == 0))
        for index, panel in enumerate(CONTENT_PANELS)
    )
    return (
        '<section id="content-workspace" class="content-workspace" aria-live="polite">'
        '<div class="workspace-heading">'
        "<h2>Research content workspace</h2>"
        "<p>Use the fixed left menu to swap this right-side content area without leaving the page.</p>"
        "</div>"
        f'<div class="content-panel-stack">{panels}</div>'
        "</section>"
    )


def _render_content_panel(panel: ContentPanel, *, active: bool) -> str:
    bullets = "".join(f"<li>{html.escape(item)}</li>" for item in panel.bullets)
    active_class = " active" if active else ""
    return (
        f'<article class="content-panel{active_class}" data-panel-id="{html.escape(panel.panel_id)}">'
        f"<h3>{html.escape(panel.title)}</h3>"
        f"<p>{html.escape(panel.lead)}</p>"
        f"<pre>{html.escape(panel.equation)}</pre>"
        f"<ul>{bullets}</ul>"
        f'<span class="panel-status">{html.escape(panel.status)}</span>'
        "</article>"
    )
