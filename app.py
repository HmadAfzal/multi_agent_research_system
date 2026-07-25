import io
import re
import time
from datetime import datetime

import streamlit as st
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)
from xml.sax.saxutils import escape as xml_escape

from pipeline import run_research_pipeline

# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Research Console",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Design tokens
#   Paper / ink / slate / hairline = base palette on a white canvas.
#   Cobalt / teal / coral = semantic state colors for the pipeline tracker
#   (active / done / error) - not decoration, they carry real status.
# ---------------------------------------------------------------------------
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }

/* The app was originally themed dark (light text on dark surfaces). Re-declaring
   Streamlit's own theme variables here overrides that at the source, so any native
   element we haven't explicitly restyled below still gets dark-on-light text. */
:root, .stApp {
  --text-color: #14181F !important;
  --background-color: #FFFFFF !important;
  --secondary-background-color: #F7F8F6 !important;
}

.stApp, [data-testid="stAppViewContainer"] {
  background: #FFFFFF;
  color: #14181F;
}
header[data-testid="stHeader"] { background: transparent !important; }
div[data-testid="stDecoration"] { display: none; }
#MainMenu, footer { visibility: hidden; }

/* Belt-and-suspenders: force the actual text nodes Streamlit renders for
   plain markdown (report/feedback body, warnings, captions) to dark ink,
   since these come from arbitrary content we don't otherwise style. */
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] span,
[data-testid="stMarkdownContainer"] strong,
[data-testid="stMarkdownContainer"] em,
[data-testid="stMarkdownContainer"] ol,
[data-testid="stMarkdownContainer"] ul,
[data-testid="stCaptionContainer"],
label, label p,
div[data-testid="stAlert"] p,
div[data-testid="stAlert"] span {
  color: #14181F !important;
}

section[data-testid="stSidebar"] {
  background: #F7F8F6;
  border-right: 1px solid #E4E7EC;
}

/* ---- eyebrow / headings ---- */
.rc-eyebrow {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.72rem;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: #2F6FED;
  margin-bottom: 0.35rem;
}
.rc-title {
  font-family: 'Space Grotesk', sans-serif;
  font-weight: 700;
  font-size: 2.3rem;
  color: #14181F;
  margin: 0 0 0.5rem 0;
  line-height: 1.1;
}
.rc-sub { color: #667085; font-size: 0.98rem; max-width: 620px; line-height: 1.5; }

[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3 {
  font-family: 'Space Grotesk', sans-serif !important;
  color: #14181F !important;
}
[data-testid="stMarkdownContainer"] a { color: #2F6FED; }
[data-testid="stMarkdownContainer"] code {
  background: #F1F2F0; padding: 0.1rem 0.35rem; border-radius: 4px;
  color: #3A4150; font-family: 'IBM Plex Mono', monospace;
}

/* ---- form / inputs ---- */
div[data-testid="stTextInput"] input, .stTextInput input {
  background: #FFFFFF !important;
  border: 1px solid #D8DCE3 !important;
  border-radius: 8px !important;
  color: #14181F !important;
  font-family: 'IBM Plex Mono', monospace !important;
  padding: 0.65rem 0.9rem !important;
}
div[data-testid="stTextInput"] input:focus {
  border-color: #2F6FED !important;
  box-shadow: 0 0 0 1px #2F6FED !important;
}
div[data-testid="stTextInput"] input::placeholder { color: #9AA3B2 !important; }

div[data-testid="stFormSubmitButton"] button {
  background: #2F6FED !important;
  color: #FFFFFF !important;
  border: none !important;
  border-radius: 8px !important;
  font-weight: 600 !important;
  font-family: 'IBM Plex Sans', sans-serif !important;
  padding: 0.65rem 1.2rem !important;
  transition: box-shadow 0.15s ease;
}
div[data-testid="stFormSubmitButton"] button p { color: #FFFFFF !important; }
div[data-testid="stFormSubmitButton"] button:hover { box-shadow: 0 0 0 3px rgba(47,111,237,0.20); }
div[data-testid="stFormSubmitButton"] button:focus-visible { outline: 2px solid #2F6FED; outline-offset: 2px; }

div[data-testid="stDownloadButton"] button {
  background: transparent !important;
  border: 1px solid #D8DCE3 !important;
  color: #14181F !important;
  border-radius: 8px !important;
  font-family: 'IBM Plex Sans', sans-serif !important;
}
div[data-testid="stDownloadButton"] button p { color: #14181F !important; }
div[data-testid="stDownloadButton"] button:hover { border-color: #2F6FED !important; color: #2F6FED !important; }
div[data-testid="stDownloadButton"] button:hover p { color: #2F6FED !important; }

/* sidebar buttons read as a list, not chrome */
section[data-testid="stSidebar"] div[data-testid="stButton"] button {
  background: transparent !important;
  border: 1px solid transparent !important;
  color: #4B5563 !important;
  text-align: left !important;
  justify-content: flex-start !important;
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: 0.78rem !important;
  padding: 0.4rem 0.55rem !important;
}
section[data-testid="stSidebar"] div[data-testid="stButton"] button p { color: #4B5563 !important; }
section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover {
  background: #EEF0ED !important;
  border-color: #D8DCE3 !important;
  color: #2F6FED !important;
}
section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover p { color: #2F6FED !important; }

/* ---- tabs ---- */
button[data-baseweb="tab"] {
  font-family: 'IBM Plex Mono', monospace;
  color: #667085 !important;
}
button[data-baseweb="tab"][aria-selected="true"] { color: #2F6FED !important; }
div[data-baseweb="tab-highlight"] { background-color: #2F6FED !important; }
div[data-baseweb="tab-border"] { background-color: #E4E7EC !important; }

/* ---- bordered containers (report / feedback cards) ---- */
div[data-testid="stVerticalBlockBorderWrapper"] {
  background: #FFFFFF !important;
  border: 1px solid #E4E7EC !important;
  border-radius: 12px !important;
  box-shadow: 0 1px 2px rgba(20,24,31,0.04);
}

[data-testid="stExpander"] {
  border: 1px solid #E4E7EC !important;
  border-radius: 10px !important;
  background: #FBFBFA !important;
}

[data-testid="stCodeBlock"] { border-radius: 10px !important; border: 1px solid #E4E7EC !important; }

div[data-testid="stAlert"] { border-radius: 10px !important; font-family: 'IBM Plex Sans', sans-serif !important; }

/* ---- pipeline tracker (signature element) ---- */
.rc-track { display: flex; align-items: flex-start; margin: 1.5rem 0 0.4rem 0; }
.rc-node { display: flex; flex-direction: column; align-items: center; flex: 1; position: relative; }
.rc-line {
  position: absolute; top: 17px; left: -50%; width: 100%; height: 2px;
  background: #E4E7EC; z-index: 1;
}
.rc-node:first-child .rc-line { display: none; }
.rc-node.done .rc-line { background: #12805C; }
.rc-dot {
  width: 34px; height: 34px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  border: 2px solid #D8DCE3; background: #FFFFFF; color: #98A2B3;
  font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem; font-weight: 600;
  z-index: 2; transition: all 0.25s ease;
}
.rc-node.active .rc-dot {
  border-color: #2F6FED; color: #2F6FED;
  animation: rc-pulse 1.4s ease-in-out infinite;
}
.rc-node.done .rc-dot { border-color: #12805C; background: #12805C; color: #FFFFFF; }
.rc-node.error .rc-dot { border-color: #D64545; color: #D64545; }
.rc-label {
  margin-top: 0.5rem; font-size: 0.75rem; letter-spacing: 0.04em; text-transform: uppercase;
  color: #98A2B3; font-family: 'IBM Plex Mono', monospace;
}
.rc-node.active .rc-label, .rc-node.done .rc-label { color: #14181F; }
@keyframes rc-pulse {
  0%, 100% { box-shadow: 0 0 0 4px rgba(47,111,237,0.14); }
  50% { box-shadow: 0 0 0 9px rgba(47,111,237,0.05); }
}
@media (prefers-reduced-motion: reduce) { .rc-node.active .rc-dot { animation: none; } }
@media (max-width: 640px) { .rc-label { font-size: 0.6rem; } .rc-title { font-size: 1.7rem; } }

/* ---- console log ---- */
.rc-console {
  background: #F7F8F6; border: 1px solid #E4E7EC; border-radius: 10px;
  padding: 0.8rem 1rem; font-family: 'IBM Plex Mono', monospace; font-size: 0.8rem;
  color: #4B5563; max-height: 190px; overflow-y: auto; margin-top: 0.9rem;
}
.rc-console .line { padding: 0.15rem 0; border-bottom: 1px dashed #E4E7EC; }
.rc-console .line:last-child { border-bottom: none; }
.rc-console .t { color: #9AA3B2; margin-right: 0.6rem; }
.rc-console::-webkit-scrollbar { width: 6px; }
.rc-console::-webkit-scrollbar-thumb { background: #D8DCE3; border-radius: 3px; }

/* ---- stat cards ---- */
.rc-stat {
  flex: 1; background: #FFFFFF; border: 1px solid #E4E7EC; border-radius: 10px;
  padding: 0.85rem 1.05rem;
}
.rc-stat .k { font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem; letter-spacing: 0.14em;
  text-transform: uppercase; color: #98A2B3; margin-bottom: 0.25rem; }
.rc-stat .v { font-family: 'Space Grotesk', sans-serif; font-size: 1.3rem; color: #14181F; }

.rc-empty {
  border: 1px dashed #D8DCE3; border-radius: 12px; padding: 2.4rem 1.5rem;
  text-align: center; color: #667085; font-size: 0.95rem;
}
"""
st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Pipeline stage model
# ---------------------------------------------------------------------------
STAGES = ["search", "read", "draft", "critique"]
STAGE_LABELS = {"search": "Search", "read": "Read", "draft": "Draft", "critique": "Critique"}
STAGE_MARKS = {"search": "01", "read": "02", "draft": "03", "critique": "04"}

# maps the step names pipeline.py's notify() sends -> (stage, new_state)
STEP_TO_STAGE = {
    "Searching for content": ("search", "active"),
    "Search results": ("search", "done"),
    "Scraping top resources": ("read", "active"),
    "Scraped content": ("read", "done"),
    "Drafting the report": ("draft", "active"),
    "Draft report": ("draft", "done"),
    "Critic reviewing report": ("critique", "active"),
    "Critic feedback": ("critique", "done"),
}


def to_text(x) -> str:
    """Chains/agents can return strings, message objects, or dicts - normalize to text."""
    if x is None:
        return ""
    if hasattr(x, "content"):
        return x.content
    if isinstance(x, dict) and "content" in x:
        return x["content"]
    return str(x)


def render_tracker(states: dict) -> str:
    nodes = []
    for key in STAGES:
        state = states.get(key, "idle")
        mark = "✓" if state == "done" else ("!" if state == "error" else STAGE_MARKS[key])
        nodes.append(
            f'<div class="rc-node {state}">'
            f'<div class="rc-line"></div>'
            f'<div class="rc-dot">{mark}</div>'
            f'<div class="rc-label">{STAGE_LABELS[key]}</div>'
            f"</div>"
        )
    return f'<div class="rc-track">{"".join(nodes)}</div>'


def render_console(lines) -> str:
    if not lines:
        return '<div class="rc-console"><div class="line">Idle — waiting for a topic.</div></div>'
    items = "".join(f'<div class="line"><span class="t">{t}</span>{s}</div>' for t, s in lines)
    return f'<div class="rc-console">{items}</div>'


def render_stats(elapsed: float, report_text: str, feedback_text: str) -> str:
    words = len(report_text.split()) if report_text else 0
    fb_words = len(feedback_text.split()) if feedback_text else 0
    return (
        '<div style="display:flex; gap:0.8rem; margin: 1rem 0 1.3rem 0;">'
        f'<div class="rc-stat"><div class="k">Runtime</div><div class="v">{elapsed:.1f}s</div></div>'
        f'<div class="rc-stat"><div class="k">Report</div><div class="v">{words} words</div></div>'
        f'<div class="rc-stat"><div class="k">Feedback</div><div class="v">{fb_words} words</div></div>'
        "</div>"
    )


# ---------------------------------------------------------------------------
# PDF export
# ---------------------------------------------------------------------------
def _inline_markup(text: str) -> str:
    """Escape a line for ReportLab's Paragraph markup, then re-enable **bold** spans."""
    escaped = xml_escape(text)
    return re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", escaped)


@st.cache_data(show_spinner=False)
def build_report_pdf(topic: str, report_text: str) -> bytes:
    """Render the markdown-style report text into an actual PDF (not just a renamed .md)."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        leftMargin=0.9 * inch,
        rightMargin=0.9 * inch,
        topMargin=0.9 * inch,
        bottomMargin=0.9 * inch,
        title=topic or "Research Report",
    )

    ink = colors.HexColor("#14181F")
    muted = colors.HexColor("#667085")
    hairline = colors.HexColor("#E4E7EC")

    base = getSampleStyleSheet()["Normal"]
    title_style = ParagraphStyle("RCTitle", parent=base, fontName="Helvetica-Bold", fontSize=20, leading=24, textColor=ink, spaceAfter=4)
    meta_style = ParagraphStyle("RCMeta", parent=base, fontSize=9, textColor=muted, spaceAfter=16)
    h1 = ParagraphStyle("RCH1", parent=base, fontName="Helvetica-Bold", fontSize=15, leading=19, textColor=ink, spaceBefore=14, spaceAfter=8)
    h2 = ParagraphStyle("RCH2", parent=base, fontName="Helvetica-Bold", fontSize=13, leading=17, textColor=ink, spaceBefore=12, spaceAfter=6)
    h3 = ParagraphStyle("RCH3", parent=base, fontName="Helvetica-Bold", fontSize=11.5, leading=15, textColor=ink, spaceBefore=10, spaceAfter=4)
    body = ParagraphStyle("RCBody", parent=base, fontName="Helvetica", fontSize=10.5, leading=15.5, textColor=ink, spaceAfter=8, alignment=TA_LEFT)
    bullet_style = ParagraphStyle("RCBullet", parent=body, spaceAfter=4)

    story = [
        Paragraph(xml_escape(topic or "Research Report"), title_style),
        Paragraph(datetime.now().strftime("Generated %b %d, %Y"), meta_style),
        HRFlowable(width="100%", thickness=0.6, color=hairline, spaceAfter=14),
    ]

    bullets: list[str] = []

    def flush_bullets():
        if bullets:
            story.append(
                ListFlowable(
                    [ListItem(Paragraph(b, bullet_style), bulletColor=ink) for b in bullets],
                    bulletType="bullet",
                    leftIndent=16,
                )
            )
            bullets.clear()

    for raw_line in (report_text or "").split("\n"):
        stripped = raw_line.strip()
        if not stripped:
            flush_bullets()
            story.append(Spacer(1, 6))
            continue
        if stripped.startswith("### "):
            flush_bullets()
            story.append(Paragraph(_inline_markup(stripped[4:]), h3))
        elif stripped.startswith("## "):
            flush_bullets()
            story.append(Paragraph(_inline_markup(stripped[3:]), h2))
        elif stripped.startswith("# "):
            flush_bullets()
            story.append(Paragraph(_inline_markup(stripped[2:]), h1))
        elif stripped.startswith(("- ", "* ")):
            bullets.append(_inline_markup(stripped[2:]))
        else:
            flush_bullets()
            story.append(Paragraph(_inline_markup(stripped), body))
    flush_bullets()

    doc.build(story)
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "history" not in st.session_state:
    st.session_state.history = []
if "selected" not in st.session_state:
    st.session_state.selected = 0

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="rc-eyebrow">Agent Console</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-family:\'Space Grotesk\',sans-serif; font-weight:700; '
        'font-size:1.05rem; color:#14181F; margin-bottom:0.7rem;">How it works</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div style='font-size:0.83rem; color:#667085; line-height:1.75;'>"
        "<strong style='color:#14181F;'>Search</strong> finds recent sources<br>"
        "<strong style='color:#14181F;'>Read</strong> scrapes the best one<br>"
        "<strong style='color:#14181F;'>Draft</strong> writes the report<br>"
        "<strong style='color:#14181F;'>Critique</strong> reviews the draft"
        "</div>",
        unsafe_allow_html=True,
    )

    if st.session_state.history:
        st.divider()
        st.markdown('<div class="rc-eyebrow">History</div>', unsafe_allow_html=True)
        for i, run in enumerate(st.session_state.history):
            marker = "▸ " if i == st.session_state.selected else "\u2007\u2007"
            topic_short = run["topic"][:28] + ("…" if len(run["topic"]) > 28 else "")
            if st.button(f"{marker}{topic_short}", key=f"hist_{i}", use_container_width=True):
                st.session_state.selected = i
            st.markdown(
                f'<div style="margin:-0.35rem 0 0.4rem 0.6rem; font-size:0.68rem; color:#9AA3B2; '
                f'font-family:\'IBM Plex Mono\',monospace;">{run.get("timestamp", "")}</div>',
                unsafe_allow_html=True,
            )
        if st.button("Clear history", use_container_width=True):
            st.session_state.history = []
            st.session_state.selected = 0

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown('<div class="rc-eyebrow">Multi-Agent Pipeline</div>', unsafe_allow_html=True)
st.markdown('<div class="rc-title">Research Console</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="rc-sub">Four agents run in sequence to find, verify, draft, and review '
    'a report on any topic — search, read, draft, critique.</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Command bar
# ---------------------------------------------------------------------------
st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)
with st.form("run_form", clear_on_submit=False):
    c1, c2 = st.columns([5, 1])
    with c1:
        topic = st.text_input(
            "Research topic",
            placeholder="e.g. Impact of AI on the semiconductor industry",
            label_visibility="collapsed",
        )
    with c2:
        submitted = st.form_submit_button("Run Research", use_container_width=True)

# ---------------------------------------------------------------------------
# Live pipeline tracker + console
# ---------------------------------------------------------------------------
tracker_slot = st.empty()
console_slot = st.empty()


def show_idle():
    tracker_slot.markdown(render_tracker({k: "idle" for k in STAGES}), unsafe_allow_html=True)
    console_slot.markdown(render_console([]), unsafe_allow_html=True)


def show_from_history(entry):
    tracker_slot.markdown(render_tracker({k: "done" for k in STAGES}), unsafe_allow_html=True)
    console_slot.markdown(render_console(entry.get("log", [])), unsafe_allow_html=True)


if not submitted:
    if st.session_state.history:
        show_from_history(st.session_state.history[min(st.session_state.selected, len(st.session_state.history) - 1)])
    else:
        show_idle()
elif not topic.strip():
    st.warning("Enter a topic first.")
    if st.session_state.history:
        show_from_history(st.session_state.history[min(st.session_state.selected, len(st.session_state.history) - 1)])
    else:
        show_idle()
else:
    stage_states = {k: "idle" for k in STAGES}
    log_lines = []
    tracker_slot.markdown(render_tracker(stage_states), unsafe_allow_html=True)
    console_slot.markdown(render_console(log_lines), unsafe_allow_html=True)

    def report_step(name, content):
        stage, state = STEP_TO_STAGE.get(name, (None, None))
        if stage:
            stage_states[stage] = state
        log_lines.append((datetime.now().strftime("%H:%M:%S"), name))
        tracker_slot.markdown(render_tracker(stage_states), unsafe_allow_html=True)
        console_slot.markdown(render_console(log_lines), unsafe_allow_html=True)

    start = time.time()
    try:
        result = run_research_pipeline(topic, status_callback=report_step)
        elapsed = time.time() - start
        for k in STAGES:
            stage_states[k] = "done"
        tracker_slot.markdown(render_tracker(stage_states), unsafe_allow_html=True)
        st.session_state.history.insert(
            0,
            {
                "topic": topic,
                "result": result,
                "elapsed": elapsed,
                "timestamp": datetime.now().strftime("%b %d · %H:%M"),
                "log": log_lines,
            },
        )
        st.session_state.selected = 0
    except Exception as e:
        for k in STAGES:
            if stage_states[k] == "active":
                stage_states[k] = "error"
        tracker_slot.markdown(render_tracker(stage_states), unsafe_allow_html=True)
        st.error(f"Something went wrong while running the pipeline: {e}")

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
if st.session_state.history:
    idx = min(st.session_state.selected, len(st.session_state.history) - 1)
    entry = st.session_state.history[idx]
    result = entry["result"]

    report_text = to_text(result.get("report"))
    feedback_text = to_text(result.get("feedback"))
    search_text = to_text(result.get("search_results"))
    scraped_text = to_text(result.get("scraped_content"))

    st.markdown(render_stats(entry.get("elapsed", 0), report_text, feedback_text), unsafe_allow_html=True)

    tab_report, tab_feedback, tab_search, tab_scraped = st.tabs(
        ["Report", "Critic feedback", "Search results", "Scraped content"]
    )

    with tab_report:
        with st.container(border=True):
            st.markdown(report_text if report_text else "_No report generated._")
        if report_text:
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.download_button(
                    "Download as Markdown",
                    data=report_text,
                    file_name=f"{entry['topic'][:40].replace(' ', '_')}_report.md",
                    mime="text/markdown",
                    use_container_width=True,
                )
            with col_b:
                st.download_button(
                    "Download as PDF",
                    data=build_report_pdf(entry["topic"], report_text),
                    file_name=f"{entry['topic'][:40].replace(' ', '_')}_report.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            with col_c:
                with st.expander("View raw / copy"):
                    st.code(report_text, language=None)

    with tab_feedback:
        with st.container(border=True):
            st.markdown(feedback_text if feedback_text else "_No feedback generated._")

    with tab_search:
        st.code(search_text if search_text else "No search results captured.", language=None)

    with tab_scraped:
        st.code(scraped_text if scraped_text else "No scraped content captured.", language=None)
else:
    st.markdown(
        '<div class="rc-empty">No research yet. Enter a topic above and click '
        "<strong>Run Research</strong> to begin.</div>",
        unsafe_allow_html=True,
    )