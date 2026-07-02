from __future__ import annotations

from dataclasses import dataclass
import html


GITHUB_REPO_URL = "https://github.com/eljja/3body"


@dataclass(frozen=True)
class MenuItem:
    panel_id: str
    label: str
    label_ko: str
    short_label: str


@dataclass(frozen=True)
class ContentPanel:
    panel_id: str
    title: str
    title_ko: str
    lead: str
    lead_ko: str
    equation: str
    bullets: tuple[str, ...]
    bullets_ko: tuple[str, ...]
    status: str
    status_ko: str


FLOATING_MENU_ITEMS: tuple[MenuItem, ...] = (
    MenuItem("threebody-answer", "Three-body answer", "삼체 답변", "3B"),
    MenuItem("closed-form-route", "Closed-form route", "닫힌형 경로", "CF"),
    MenuItem("collatz-conjecture", "Collatz Conjecture", "콜라츠 추측", "C"),
    MenuItem("progress-map", "Progress", "진행도", "P"),
    MenuItem("public-audit", "Audit", "감사", "A"),
    MenuItem("build-provenance", "Build", "빌드", "B"),
)


CONTENT_PANELS: tuple[ContentPanel, ...] = (
    ContentPanel(
        panel_id="threebody-answer",
        title="Three-body target answer",
        title_ko="삼체 목표시각 답변",
        lead=(
            "The current engine answers the original finite-time question: compute deterministic "
            "positions when the flow remains resolved, otherwise report the pushed-forward target "
            "distribution under the declared initial uncertainty."
        ),
        lead_ko=(
            "현재 엔진은 원래 목표인 유한시간 질문에 답한다. 흐름이 충분히 해상되면 "
            "결정론적 위치를 계산하고, 불확실성이 지배적이면 선언된 초기 불확실성을 "
            "목표시각까지 밀어낸 확률분포를 보고한다."
        ),
        equation="r_i(t) = Pi_{r_i} Phi_t(x(0));  Law(X_t) = (Phi_t)# Law(X_0)",
        bullets=(
            "Compact answer: target positions, probability regions, pair geometry, and center-of-mass readout.",
            "Random challenge: threebody random-demo generates an arbitrary non-collisional case and checks predictions against a stricter reference.",
            "Decision gate: target_readout_decision chooses point positions, probability regions, deterministic-only, or unresolved.",
            "Predictability budget: target_sensitivity_budget ties the answer to horizon, tolerance, FTLE, and close-approach diagnostics.",
        ),
        bullets_ko=(
            "압축 답변: 목표 위치, 확률 영역, 쌍 기하, 질량중심 좌표계를 함께 제공한다.",
            "랜덤 챌린지: threebody random-demo가 비충돌 임의 사례를 만들고 더 엄격한 기준 적분과 비교한다.",
            "판정 gate: target_readout_decision이 점 위치, 확률 영역, 결정론 전용, 미해결 중 하나를 고른다.",
            "예측 가능성 예산: target_sensitivity_budget이 horizon, tolerance, FTLE, 근접조우 진단을 연결한다.",
        ),
        status="implemented",
        status_ko="구현됨",
    ),
    ContentPanel(
        panel_id="closed-form-route",
        title="Global closed-form route",
        title_ko="전역 닫힌형 경로",
        lead=(
            "The defensible global route is not a finite elementary formula. It is a "
            "Sundman-style regularized convergent series contract, gated by no initial "
            "binary collision and a nonzero-angular-momentum condition until collision "
            "charts are implemented."
        ),
        lead_ko=(
            "방어 가능한 전역 경로는 유한 초등함수 공식이 아니다. 현재는 초기 이중충돌이 "
            "없고 각운동량이 0이 아닌 경우에 한해 Sundman식 정규화 수렴급수 연구 계약으로 "
            "제한한다."
        ),
        equation="x(tau)=sum_{k>=0} a_k tau^k;  r_i(t)=Pi_{r_i} Phi_t(x(0))",
        bullets=(
            "API: assess_three_body_global_closed_form_claim returns a machine-readable admissibility certificate.",
            "Boundary: elementary closed-form global formula is not promoted.",
            "Next proof work: coefficient recurrences, collision charts, and interval truncation bounds.",
        ),
        bullets_ko=(
            "API: assess_three_body_global_closed_form_claim은 기계판독 admissibility certificate를 반환한다.",
            "경계: 초등함수 전역 공식은 주장하지 않는다.",
            "다음 증명 작업: 계수 점화식, 충돌 chart, 구간 truncation bound.",
        ),
        status="contract-implemented",
        status_ko="계약 구현",
    ),
    ContentPanel(
        panel_id="collatz-conjecture",
        title="Collatz Conjecture",
        title_ko="콜라츠 추측",
        lead=(
            "This panel organizes Collatz exploration as symbolic dynamics and descent certificates. "
            "It deliberately separates exhaustive finite checks from any global termination claim."
        ),
        lead_ko=(
            "이 패널은 콜라츠 탐색을 기호 동역학과 감소 certificate 문제로 정리한다. "
            "유한 범위 exhaustive check와 전역 종료 주장을 분리한다."
        ),
        equation="T(n)=n/2 if n even;  T(n)=3n+1 if n odd",
        bullets=(
            "Use residue-class transition graphs to expose memory and drift structure.",
            "Record stopping-time distributions and counterexample search bounds as auditable artifacts.",
            "Only promote local descent certificates when every branch in the declared box is covered.",
        ),
        bullets_ko=(
            "나머지류 전이 그래프로 memory와 drift 구조를 드러낸다.",
            "정지시간 분포와 반례 탐색 범위를 감사 가능한 산출물로 기록한다.",
            "선언된 box의 모든 branch가 덮일 때만 local descent certificate를 승격한다.",
        ),
        status="research-outline",
        status_ko="연구 개요",
    ),
)


def render_floating_nav() -> str:
    buttons = "\n".join(
        (
            '<button type="button" class="nav-panel-button" '
            f'data-panel-target="{html.escape(item.panel_id)}" '
            f'data-short="{html.escape(item.short_label)}">'
            f'<span data-lang="en">{html.escape(item.label)}</span>'
            f'<span data-lang="ko">{html.escape(item.label_ko)}</span></button>'
        )
        for item in FLOATING_MENU_ITEMS
    )
    return (
        '<nav class="floating-nav" aria-label="Content panel navigation">'
        f"{buttons}"
        f'<a class="repo-link" href="{html.escape(GITHUB_REPO_URL)}" data-short="GH" '
        'target="_blank" rel="noopener noreferrer">'
        '<span data-lang="en">GitHub repo</span><span data-lang="ko">GitHub 저장소</span></a>'
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
        '<h2><span data-lang="en">Research content workspace</span><span data-lang="ko">연구 내용 작업공간</span></h2>'
        '<p data-lang="en">Use the fixed left menu to swap this right-side content area without leaving the page.</p>'
        '<p data-lang="ko">왼쪽 고정 메뉴로 페이지를 이동하지 않고 오른쪽 내용을 교체합니다.</p>'
        "</div>"
        f'<div class="content-panel-stack">{panels}</div>'
        "</section>"
    )


def _render_content_panel(panel: ContentPanel, *, active: bool) -> str:
    bullets = "".join(f"<li>{html.escape(item)}</li>" for item in panel.bullets)
    bullets_ko = "".join(f"<li>{html.escape(item)}</li>" for item in panel.bullets_ko)
    active_class = " active" if active else ""
    return (
        f'<article class="content-panel{active_class}" data-panel-id="{html.escape(panel.panel_id)}">'
        f'<h3><span data-lang="en">{html.escape(panel.title)}</span><span data-lang="ko">{html.escape(panel.title_ko)}</span></h3>'
        f'<p data-lang="en">{html.escape(panel.lead)}</p>'
        f'<p data-lang="ko">{html.escape(panel.lead_ko)}</p>'
        f"<pre>{html.escape(panel.equation)}</pre>"
        f'<ul data-lang="en">{bullets}</ul>'
        f'<ul data-lang="ko">{bullets_ko}</ul>'
        f'<span class="panel-status"><span data-lang="en">{html.escape(panel.status)}</span><span data-lang="ko">{html.escape(panel.status_ko)}</span></span>'
        "</article>"
    )
