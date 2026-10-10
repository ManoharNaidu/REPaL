#!/usr/bin/env python3
"""Build 2026-10-10-project-update.pptx, the slide deck for the v3 video transcript.

usage:  python update_video/build_pptx.py [--refresh-chart]
reads   2026-10-10-video-transcript-v3.md   (speaker notes are copied verbatim from it)
writes  2026-10-10-project-update.pptx      (repo root, overwritten on every run)
        update_video/assets/f1_comparison.png  (300 dpi, only re-rendered if missing or --refresh-chart)
Every slide is built on the blank layout (slide_layouts[6]); all shapes are placed explicitly. Idempotent.
"""
import argparse, os, re, subprocess, sys

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

# ----------------------------------------------------------------------------- design system
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TRANSCRIPT = os.path.join(ROOT, "2026-10-10-video-transcript-v3.md")
OUT_PPTX = os.path.join(ROOT, "2026-10-10-project-update.pptx")
CHART_PNG = os.path.join(HERE, "assets", "f1_comparison.png")

SLIDE_W, SLIDE_H = 13.333, 7.5
MARGIN_L, MARGIN_R, MARGIN_T, MARGIN_B = 0.6, 0.6, 0.55, 0.5
CONTENT_W = SLIDE_W - MARGIN_L - MARGIN_R
CONTENT_TOP, CONTENT_BOTTOM = 1.7, 6.6          # body area; the slide number sits below, inside the bottom margin
TITLE_H, RULE_Y = 0.7, 1.35
NUM_Y, NUM_H = 6.7, 0.3

BG_NAVY, BG_WHITE = "0E1525", "FFFFFF"
ACCENT, AMBER = "4C8BF5", "E8B931"
TEXT_ON_WHITE, TEXT_ON_NAVY = "1B2430", "E6ECF5"
MUTED_ON_WHITE, MUTED_ON_NAVY = "6B7684", "9AA6B8"
PANEL_NAVY = "17223A"            # raised card on navy
PANEL_LIGHT = "F2F5FA"           # raised card on white
PLACEHOLDER_FILL = "FBEFC4"      # light amber for [FILL] boxes
PAPER_BAR = "B7C0CC"             # neutral bar for the paper's numbers in the chart

FONT, MONO = "Calibri", "Consolas"
SIZE_TITLE, SIZE_TITLE_BIG, SIZE_SUB = 34, 48, 22
SIZE_BODY, SIZE_LABEL, SIZE_SMALL = 20, 16, 16
SIZE_HERO = 56
TERMINAL_BG, TERMINAL_FG, TERMINAL_PROMPT = "0B1020", "D7E0EE", "7FB0FF"
RADIUS = 0.08


# Real values for the transcript's [FILL] blanks, taken from the repository on 2026-10-10:
#   environment : /venv/main on the current 2-GPU instance (2x RTX 5090, Python 3.12.14, torch 2.11.0+cu128); the earlier
#                 instance's results/logs/pip_install.log also shows Python 3.12 and torch 2.11.0+cu128. The GPU model is not
#                 written in the run logs themselves.
#   NYT         : data/nyt_1/test.json = 2,500 instances, 25 relations (tools/build_nyt_defon.py docstring agrees)
#   annotation  : arxiv_re/*annotation-sheet*.csv has 100 rows and every label cell is blank -> 0 labelled
ENV_TEXT = "two NVIDIA RTX 5090 GPUs, Python 3.12, PyTorch 2.11"
NYT_N, NYT_K = "2,500", "25"
SUBSTITUTIONS = [   # (transcript text, replacement) applied to the speaker notes
    ("[FILL: GPU model, Python version, PyTorch version]", ENV_TEXT),
    ("[FILL: N] sentences and [FILL: K] relations", f"{NYT_N} sentences and {NYT_K} relations"),
    ("So far I have labelled [FILL: N] sentences.", "The annotation sheet is ready, and labelling starts next."),
    ("[FILL: partly labelled / ready to label]", "ready to label"),
]
RESOLVED_CUE = '[If you have labelled none, replace the "So far I have labelled" sentence with: "The annotation sheet is ready, and labelling starts next."]'


def apply_fills(text):
    for old, new in SUBSTITUTIONS:
        text = text.replace(old, new)
    return text.replace(RESOLVED_CUE + "\n\n", "").replace(RESOLVED_CUE, "")


def rgb(h):
    return RGBColor.from_string(h)


def I(x):
    return Inches(x)


# ----------------------------------------------------------------------------- low-level helpers
def flat(shape):
    """Drop the theme <p:style> reference so no inherited shadow/effect is drawn (fill and line are set explicitly)."""
    st = shape._element.find(qn("p:style"))
    if st is not None:
        shape._element.remove(st)
    return shape


def new_slide(prs, bg):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = rgb(bg)
    return s


def add_rect(slide, x, y, w, h, fill, line=None, rounded=False, line_w=1.0, name=None):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE, I(x), I(y), I(w), I(h))
    if rounded:
        shp.adjustments[0] = RADIUS
    shp.fill.solid(); shp.fill.fore_color.rgb = rgb(fill)
    if line:
        shp.line.color.rgb = rgb(line); shp.line.width = Pt(line_w)
    else:
        shp.line.fill.background()
    shp.shadow.inherit = False
    flat(shp)
    if name:
        shp.name = name
    return shp


def add_text(slide, x, y, w, h, runs, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=1.05, pad=0.0):
    """runs: list of paragraphs; each paragraph is a list of (text, dict(size,color,bold,italic,font))."""
    tb = slide.shapes.add_textbox(I(x), I(y), I(w), I(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = I(pad)
    tf.margin_top = tf.margin_bottom = I(pad)
    for i, para in enumerate(runs):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = spacing
        for text, st in para:
            r = p.add_run(); r.text = text
            f = r.font
            f.name = st.get("font", FONT); f.size = Pt(st.get("size", SIZE_BODY))
            f.bold = st.get("bold", False); f.italic = st.get("italic", False)
            f.color.rgb = rgb(st.get("color", TEXT_ON_WHITE))
    return tb


def T(text, **st):
    return (text, st)


def add_rule(slide, x1, x2, y, color=ACCENT, width=1.0):
    ln = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, I(x1), I(y), I(x2), I(y))
    ln.line.color.rgb = rgb(color); ln.line.width = Pt(width)
    return flat(ln)


def set_notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def text_width_in(text, size, bold=False):
    """Rendered width in inches (PIL with Carlito if present, otherwise a conservative estimate)."""
    try:
        from PIL import ImageFont
        path = subprocess.run(["fc-match", "-f", "%{file}", "Carlito:bold" if bold else "Carlito"],
                              capture_output=True, text=True, timeout=5).stdout
        return ImageFont.truetype(path, 1000).getlength(text) / 1000 * size / 72
    except Exception:
        return len(text) * size / 72 * 0.55


# ----------------------------------------------------------------------------- slide chrome and components
def add_title_slide(prs, title, subtitle):
    s = new_slide(prs, BG_NAVY)
    add_rect(s, MARGIN_L, 2.0, 1.2, 0.08, ACCENT)
    tb = s.shapes.add_textbox(I(MARGIN_L), I(2.3), I(CONTENT_W), I(2.3))
    tf = tb.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]; p.line_spacing = 1.0
    first, second = title.split(" \u2014 ", 1)          # break after the em dash so "Zero-Shot" is not split
    for i, part in enumerate((first + " \u2014", second)):
        if i:
            p.add_line_break()
        r = p.add_run(); r.text = part
        r.font.name = FONT; r.font.size = Pt(SIZE_TITLE_BIG); r.font.bold = True; r.font.color.rgb = rgb(TEXT_ON_NAVY)
    add_rule(s, MARGIN_L, SLIDE_W - MARGIN_R, 4.85)
    add_text(s, MARGIN_L, 5.05, CONTENT_W, 0.9, [[T(subtitle, size=SIZE_SUB, color=MUTED_ON_NAVY)]])
    return s


def add_content_slide(prs, title, number, body_items=None, dark=False):
    s = new_slide(prs, BG_NAVY if dark else BG_WHITE)
    fg, muted = (TEXT_ON_NAVY, MUTED_ON_NAVY) if dark else (TEXT_ON_WHITE, MUTED_ON_WHITE)
    add_text(s, MARGIN_L, MARGIN_T, CONTENT_W, TITLE_H, [[T(title, size=SIZE_TITLE, bold=True, color=fg)]], anchor=MSO_ANCHOR.MIDDLE)
    add_rule(s, MARGIN_L, SLIDE_W - MARGIN_R, RULE_Y)
    add_text(s, SLIDE_W - MARGIN_R - 0.8, NUM_Y, 0.8, NUM_H, [[T(str(number), size=SIZE_SMALL, color=muted)]],
             align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)
    if body_items:
        y = CONTENT_TOP + 0.1
        for item in body_items:
            add_text(s, MARGIN_L, y, CONTENT_W, 0.6, [[T(item, size=SIZE_BODY, color=fg)]])
            y += 0.75
    return s


def add_stat_tile(slide, x, y, w, h, value, label, dark=False):
    add_rect(slide, x, y, w, h, PANEL_NAVY if dark else PANEL_LIGHT, rounded=True)
    add_rect(slide, x, y + 0.25, 0.07, h - 0.5, ACCENT)
    add_text(slide, x + 0.3, y + 0.15, w - 0.45, h * 0.55, [[T(value, size=SIZE_HERO, bold=True, color=AMBER)]], anchor=MSO_ANCHOR.MIDDLE)
    add_text(slide, x + 0.3, y + h * 0.58, w - 0.45, h * 0.36, [[T(label, size=SIZE_LABEL, color=TEXT_ON_NAVY if dark else MUTED_ON_WHITE)]],
             anchor=MSO_ANCHOR.TOP)


def add_placeholder(slide, x, y, w, h, text, size=SIZE_BODY):
    """Visible amber box the user must replace before recording (name used by the verifier)."""
    box = add_rect(slide, x, y, w, h, PLACEHOLDER_FILL, line=AMBER, rounded=True, line_w=1.5, name="FILL_PLACEHOLDER")
    tf = box.text_frame
    tf.margin_left = tf.margin_right = I(0.12); tf.margin_top = tf.margin_bottom = I(0.04)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE; tf.word_wrap = True
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = text
    r.font.name = FONT; r.font.size = Pt(size); r.font.bold = True; r.font.color.rgb = rgb(TEXT_ON_WHITE)
    return box


def add_terminal_box(slide, x, y, w, h, commands):
    """Terminal-style panel; commands = list of command strings (each may contain newlines for continuation lines)."""
    add_rect(slide, x, y, w, h, TERMINAL_BG, rounded=True)
    for i, c in enumerate(("FF5F57", "FEBC2E", "28C840")):
        d = slide.shapes.add_shape(MSO_SHAPE.OVAL, I(x + 0.25 + i * 0.3), I(y + 0.22), I(0.16), I(0.16))
        d.fill.solid(); d.fill.fore_color.rgb = rgb(c); d.line.fill.background(); d.shadow.inherit = False; flat(d)
    paras = []
    for cmd in commands:
        for j, line in enumerate(cmd.split("\n")):
            paras.append([T("$ " if j == 0 else "  ", size=SIZE_SMALL, font=MONO, color=TERMINAL_PROMPT, bold=True),
                          T(line, size=SIZE_SMALL, font=MONO, color=TERMINAL_FG)])
        paras.append([T(" ", size=8, font=MONO)])     # small gap between commands
    add_text(slide, x + 0.3, y + 0.7, w - 0.5, h - 0.85, paras, spacing=1.1)


def add_bar_chart(path, refresh=False):
    """Grouped bar chart (my F1 vs paper F1). Rendered once to PNG (300 dpi); reused if it already exists."""
    if os.path.exists(path) and not refresh:
        return path
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    font_manager._load_fontmanager(try_read_cache=False)     # pick up fonts installed after the cache was written
    os.makedirs(os.path.dirname(path), exist_ok=True)
    plt.rcParams["font.family"] = ["Carlito", "Calibri", "DejaVu Sans"]
    labels, mine, paper = ["FewRel", "WikiZSL"], [69.6, 45.9], [74.6, 47.8]
    fig, ax = plt.subplots(figsize=(6.4, 3.9), dpi=300)
    xs, bw = range(len(labels)), 0.34
    b1 = ax.bar([x - bw / 2 - 0.02 for x in xs], mine, bw, color="#" + ACCENT, label="My replication")
    b2 = ax.bar([x + bw / 2 + 0.02 for x in xs], paper, bw, color="#" + PAPER_BAR, label="Paper")
    for bars in (b1, b2):
        for b in bars:
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 1.2, f"{b.get_height():.1f}", ha="center", va="bottom",
                    fontsize=13, fontweight="bold", color="#" + TEXT_ON_WHITE)
    ax.set_xticks(list(xs)); ax.set_xticklabels(labels, fontsize=14, color="#" + TEXT_ON_WHITE)
    ax.set_ylim(0, 90); ax.set_yticks([0, 20, 40, 60, 80]); ax.tick_params(axis="y", labelsize=12, colors="#" + MUTED_ON_WHITE, length=0)
    ax.set_ylabel("F1 (%), follow-up stage", fontsize=12, color="#" + MUTED_ON_WHITE)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color("#C9D1DC"); ax.yaxis.grid(True, color="#E3E8EF", linewidth=0.8); ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=12, loc="upper right", ncol=2)
    fig.tight_layout()
    fig.savefig(path, dpi=300, facecolor="white")
    plt.close(fig)
    return path


def add_results_table(slide, x, y, w, rows):
    """Small drawn table: header + rows of (dataset, mine, paper). Numbers in amber (highlight figures)."""
    cols = [w * 0.42, w * 0.29, w * 0.29]
    row_h = 0.8
    heads = ["Follow-up F1 (%)", "Mine", "Paper"]
    cx = x
    for c, hd in zip(cols, heads):
        add_rect(slide, cx, y, c, row_h * 0.75, TEXT_ON_WHITE)
        add_text(slide, cx + 0.15, y, c - 0.2, row_h * 0.75, [[T(hd, size=SIZE_LABEL, bold=True, color=TEXT_ON_NAVY)]],
                 anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.LEFT if hd.startswith("Follow") else PP_ALIGN.CENTER)
        cx += c
    yy = y + row_h * 0.75
    for i, (name, mine, paper) in enumerate(rows):
        add_rect(slide, x, yy, w, row_h, PANEL_LIGHT if i % 2 == 0 else BG_WHITE)
        add_text(slide, x + 0.15, yy, cols[0] - 0.2, row_h, [[T(name, size=SIZE_BODY, bold=True)]], anchor=MSO_ANCHOR.MIDDLE)
        add_text(slide, x + cols[0], yy, cols[1], row_h, [[T(mine, size=32, bold=True, color=AMBER)]],
                 anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER)
        add_text(slide, x + cols[0] + cols[1], yy, cols[2], row_h, [[T(paper, size=SIZE_BODY + 4, color=MUTED_ON_WHITE)]],
                 anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER)
        yy += row_h
    add_rule(slide, x, x + w, yy, color="C9D1DC", width=0.75)
    return yy


# ----------------------------------------------------------------------------- transcript parsing (speaker notes)
def parse_transcript(path):
    lines = open(path, encoding="utf-8").read().split("\n")
    sections, cur = {}, None
    for ln in lines:
        m = re.match(r"^## (\d+:\d+-\d+:\d+)\s+.*$", ln)
        if m:
            cur = m.group(1); sections[cur] = []
        elif ln.startswith("## If asked"):
            cur = "ifasked"; sections[cur] = []
        elif ln.startswith("## ") or ln.strip() == "---":
            cur = None
        elif cur:
            sections[cur].append(ln)
    return {k: "\n".join(v).strip("\n") for k, v in sections.items()}


def timing(label, part=""):
    return "TIMING: " + label.replace("-", "–") + (f" ({part})" if part else "")


# ----------------------------------------------------------------------------- the deck
def build(prs, notes):
    # 1 --- title
    s = add_title_slide(prs, "REPaL: Reproduction and Extension — Zero-Shot Relation Extraction",
                        "COMP8240 Project Update — Manohar Naidu Bheesetti — 2026-10-10")
    set_notes(s, "All blanks were filled from the repository on 2026-10-10. Before recording, check slides 6, 7, 8, 9 against your own records.")

    # 2 --- introduction
    s = add_content_slide(prs, "Reproducing and Extending REPaL", 2)
    rows = [("PAPER", "EMNLP 2024 · Zhou et al. · UIUC + UVA"),
            ("TASK", "Zero-shot relation extraction from a written definition"),
            ("WHY CHOSEN", "Public code and data; can be pointed at new domains")]
    y = CONTENT_TOP + 0.15
    for label, text in rows:
        add_rect(s, MARGIN_L, y + 0.05, 0.07, 1.0, ACCENT)
        add_text(s, MARGIN_L + 0.3, y, 7.3, 0.4, [[T(label, size=SIZE_LABEL, bold=True, color=ACCENT)]])
        add_text(s, MARGIN_L + 0.3, y + 0.42, 7.3, 0.8, [[T(text, size=SIZE_BODY + 2)]])
        y += 1.6
    add_rect(s, 8.55, CONTENT_TOP + 0.15, 4.18, 4.55, BG_NAVY, rounded=True)
    add_text(s, 8.85, CONTENT_TOP + 0.3, 1.2, 1.3, [[T("“", size=96, bold=True, color=ACCENT)]], spacing=0.8)
    add_text(s, 8.85, CONTENT_TOP + 1.55, 3.6, 2.8, [[T("No labelled relation instances.", size=36, bold=True, color=TEXT_ON_NAVY)]],
             spacing=1.05)
    set_notes(s, timing("0:00-0:30") + "\n" + notes["0:00-0:30"])

    # 3 --- the paper's datasets
    s = add_content_slide(prs, "The paper's datasets", 3)
    cards = [("DefOn-FewRel", "Built from FewRel · Wikipedia sentences", "80", "relations", "5 held-out test groups"),
             ("DefOn-WikiZSL", "Built from WikiZSL · Wikidata", "3 × 15", "relations", "3 test groups of 15 relations")]
    cw, gap = 5.95, 0.23
    for i, (name, src, hero, unit, groups) in enumerate(cards):
        x = MARGIN_L + i * (cw + gap)
        add_rect(s, x, CONTENT_TOP, cw, 3.55, PANEL_LIGHT, rounded=True)
        add_rect(s, x, CONTENT_TOP + 0.3, 0.07, 2.95, ACCENT)
        add_text(s, x + 0.35, CONTENT_TOP + 0.25, cw - 0.6, 0.55, [[T(name, size=28, bold=True)]])
        add_text(s, x + 0.35, CONTENT_TOP + 0.85, cw - 0.6, 0.45, [[T(src, size=SIZE_BODY, color=MUTED_ON_WHITE)]])
        add_text(s, x + 0.35, CONTENT_TOP + 1.4, cw - 0.6, 1.2,
                 [[T(hero, size=SIZE_HERO + 8, bold=True, color=AMBER), T("  " + unit, size=SIZE_BODY, color=MUTED_ON_WHITE)]],
                 anchor=MSO_ANCHOR.MIDDLE)
        add_text(s, x + 0.35, CONTENT_TOP + 2.7, cw - 0.6, 0.5, [[T(groups, size=SIZE_BODY, bold=True, color=ACCENT)]])
    add_rect(s, MARGIN_L, 5.55, CONTENT_W, 0.95, BG_NAVY, rounded=True)
    add_text(s, MARGIN_L + 0.3, 5.55, CONTENT_W - 0.6, 0.95,
             [[T("Evaluation: ", size=SIZE_BODY, bold=True, color=ACCENT),
               T("each test relation is the target in turn, the others are negatives; precision, recall and F1 are averaged.",
                 size=SIZE_BODY, color=TEXT_ON_NAVY)]], anchor=MSO_ANCHOR.MIDDLE)
    set_notes(s, timing("0:30-1:15") + "\n" + notes["0:30-1:15"])

    # 4 --- architecture (spoken text up to the terminal cue)
    s = add_content_slide(prs, "How REPaL works", 4)
    boxes = [("1", "Write examples", "An LLM reads the definition and writes tagged example sentences"),
             ("2", "Train a small model", "RoBERTa-large, fine-tuned for NLI, judges sentence vs. definition"),
             ("3", "Feedback round", "A sample of its predictions returns to the LLM: new examples and negatives, then retrain")]
    bw, aw = 3.55, 0.74
    for i, (n, head, body) in enumerate(boxes):
        x = MARGIN_L + i * (bw + aw)
        add_rect(s, x, CONTENT_TOP + 0.1, bw, 3.5, PANEL_LIGHT, rounded=True, line=ACCENT, line_w=1.25)
        badge = add_rect(s, x + 0.3, CONTENT_TOP + 0.4, 0.62, 0.62, ACCENT, rounded=True)
        add_text(s, x + 0.3, CONTENT_TOP + 0.4, 0.62, 0.62, [[T(n, size=24, bold=True, color="FFFFFF")]],
                 align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        add_text(s, x + 0.3, CONTENT_TOP + 1.2, bw - 0.55, 0.5, [[T(head, size=24, bold=True)]])
        add_text(s, x + 0.3, CONTENT_TOP + 1.85, bw - 0.55, 1.6, [[T(body, size=SIZE_BODY, color=TEXT_ON_WHITE)]])
        if i < 2:
            ar = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, I(x + bw + 0.1), I(CONTENT_TOP + 1.65), I(aw - 0.2), I(0.55))
            ar.fill.solid(); ar.fill.fore_color.rgb = rgb(ACCENT); ar.line.fill.background(); ar.shadow.inherit = False; flat(ar)
    add_text(s, MARGIN_L, 5.65, CONTENT_W, 0.6, [[T("No human-labelled training data.", size=26, bold=True, color=ACCENT)]],
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    sec = notes["1:15-2:45"]; cut = sec.index("[Terminal:")
    set_notes(s, timing("1:15-2:45", "part 1") + "\n" + sec[:cut].rstrip("\n"))
    part2 = sec[cut:]

    # 5 --- code and a finished run
    s = add_content_slide(prs, "Code and a finished run", 5)
    add_text(s, MARGIN_L, CONTENT_TOP + 0.1, 4.5, 3.2,
             [[T("Authors' code is public; I forked it.", size=SIZE_BODY + 2, bold=True)],
              [T(" ", size=10)],
              [T("One Python driver replaces the authors' shell scripts and runs every split.", size=SIZE_BODY + 2)]], spacing=1.1)
    add_terminal_box(s, 5.45, CONTENT_TOP + 0.05, 7.28, 3.95, [
        "python run_experiments.py --dry-run \\\n  --datasets fewrel_defon --splits 1 \\\n  --stages initial \\\n  --data-root reproduce_main_data/data \\\n  --device-profile gpu",
        "tail -n 5 \\\n  results/fewrel_defon_1/initial/run.log",
        "cat \\\n  results/fewrel_defon_1/initial/metrics.json"])
    add_text(s, MARGIN_L, 6.0, CONTENT_W, 0.5, [[T("Finished run — one split takes hours.", size=SIZE_BODY, italic=True, color=MUTED_ON_WHITE)]],
             anchor=MSO_ANCHOR.MIDDLE)
    set_notes(s, timing("1:15-2:45", "part 2") + "\n" + part2)

    # 6 --- replication status
    s = add_content_slide(prs, "Replication status", 6)
    add_results_table(s, MARGIN_L, CONTENT_TOP + 0.1, 5.3, [("FewRel", "69.6", "74.6"), ("WikiZSL", "45.9", "47.8")])
    add_text(s, MARGIN_L, CONTENT_TOP + 2.55, 5.3, 1.0,
             [[T("All eight splits finished, using the authors' cached GPT-4o examples.", size=SIZE_BODY, color=MUTED_ON_WHITE)]])
    s.shapes.add_picture(CHART_PNG, I(6.25), I(CONTENT_TOP), width=I(6.48))
    add_text(s, MARGIN_L, 5.95, 3.4, 0.55, [[T("Run on rented cloud GPUs:", size=SIZE_BODY, bold=True)]], anchor=MSO_ANCHOR.MIDDLE)
    add_rect(s, MARGIN_L + 3.45, 5.95, 8.68, 0.55, BG_NAVY, rounded=True)
    add_text(s, MARGIN_L + 3.7, 5.95, 8.3, 0.55, [[T("2\u00d7 NVIDIA RTX 5090  \u00b7  Python 3.12  \u00b7  PyTorch 2.11", size=SIZE_BODY, bold=True, color=TEXT_ON_NAVY)]],
             anchor=MSO_ANCHOR.MIDDLE)
    set_notes(s, timing("2:45-3:30") + "\n" + notes["2:45-3:30"])

    # 7 --- new datasets
    s = add_content_slide(prs, "New datasets", 7)
    cw, gap = 3.93, 0.17
    chips = [("SemEval-2010 Task 8", "8,851", "sentences \u00b7 17 directed relations \u00b7 \u201cOther\u201d removed"),
             ("NYT", NYT_N, f"sentences \u00b7 {NYT_K} relations"),
             ("arXiv \u2014 my own dataset", None, "See next slide")]
    for i, (name, hero, sub) in enumerate(chips):
        x = MARGIN_L + i * (cw + gap)
        add_rect(s, x, CONTENT_TOP, cw, 2.3, PANEL_LIGHT, rounded=True)
        add_rect(s, x, CONTENT_TOP + 0.25, 0.07, 1.8, ACCENT)
        add_text(s, x + 0.3, CONTENT_TOP + 0.12, cw - 0.45, 0.5, [[T(name, size=SIZE_BODY, bold=True, color=ACCENT)]])
        if hero:
            add_text(s, x + 0.3, CONTENT_TOP + 0.65, cw - 0.45, 0.9, [[T(hero, size=SIZE_HERO, bold=True, color=AMBER)]],
                     anchor=MSO_ANCHOR.MIDDLE)
            add_text(s, x + 0.3, CONTENT_TOP + 1.55, cw - 0.45, 0.7, [[T(sub, size=SIZE_LABEL, color=MUTED_ON_WHITE)]])
        else:
            add_text(s, x + 0.3, CONTENT_TOP + 0.85, cw - 0.45, 1.2, [[T(sub, size=SIZE_BODY + 2, color=TEXT_ON_WHITE)]])
    add_text(s, MARGIN_L, 4.3, CONTENT_W, 0.4, [[T("RESULTS (F1, %)", size=SIZE_LABEL, bold=True, color=ACCENT)]])
    add_rule(s, MARGIN_L, SLIDE_W - MARGIN_R, 4.75, color="C9D1DC", width=0.75)
    res = [("19 \u2192 31", "SemEval F1, with feedback"), ("\u2248 47", "NYT F1"), ("Qwen2.5", "local model replaces GPT-4o")]
    for i, (v, l) in enumerate(res):
        x = MARGIN_L + i * (cw + gap)
        add_text(s, x, 4.95, cw, 0.95, [[T(v, size=SIZE_HERO, bold=True, color=AMBER)]], anchor=MSO_ANCHOR.MIDDLE)
        add_text(s, x, 5.95, cw, 0.5, [[T(l, size=SIZE_LABEL, color=MUTED_ON_WHITE)]])
    set_notes(s, timing("3:30-4:20") + "\n" + notes["3:30-4:20"])

    # 8 --- own dataset
    s = add_content_slide(prs, "Own dataset: arXiv scientific literature", 8)
    tiles = [("397", "abstracts"), ("2,846", "sentences"), ("6", "relations"), ("100", "sentence annotation sheet")]
    tw, tg = 2.9, 0.177
    for i, (v, l) in enumerate(tiles):
        add_stat_tile(s, MARGIN_L + i * (tw + tg), CONTENT_TOP, tw, 1.85, v, l)
    add_text(s, MARGIN_L, 3.85, CONTENT_W, 0.4, [[T("RELATIONS", size=SIZE_LABEL, bold=True, color=ACCENT)]])
    add_text(s, MARGIN_L, 4.25, CONTENT_W, 0.5,
             [[T("evaluated_on · outperforms · achieves_result · builds_on · applied_to_task · uses_component",
                 size=SIZE_BODY, bold=True)]], anchor=MSO_ANCHOR.MIDDLE)
    add_rule(s, MARGIN_L, SLIDE_W - MARGIN_R, 4.95, color="C9D1DC", width=0.75)
    add_text(s, MARGIN_L, 5.1, 3.4, 0.9, [[T("Annotation so far:", size=SIZE_BODY, bold=True)]], anchor=MSO_ANCHOR.MIDDLE)
    add_text(s, MARGIN_L + 3.4, 5.1, 2.6, 0.9, [[T("0 / 100", size=48, bold=True, color=AMBER)]], anchor=MSO_ANCHOR.MIDDLE)
    add_text(s, MARGIN_L + 6.1, 5.1, 6.0, 0.9, [[T("sentences labelled. The sheet is ready, and labelling starts next.", size=SIZE_BODY,
                                                  color=MUTED_ON_WHITE)]], anchor=MSO_ANCHOR.MIDDLE)
    set_notes(s, timing("4:20-4:50") + "\n" + notes["4:20-4:50"])

    # 9 --- wrap-up (navy)
    s = add_content_slide(prs, "Wrap-up", 9, dark=True)
    rows = ["Replication works", "Two extra datasets are done", "Own dataset is built and ready to label"]
    y = CONTENT_TOP + 0.1
    for i, text in enumerate(rows):
        add_rect(s, MARGIN_L, y, CONTENT_W, 0.95, PANEL_NAVY, rounded=True)
        add_rect(s, MARGIN_L + 0.3, y + 0.24, 0.47, 0.47, ACCENT, rounded=True)
        add_text(s, MARGIN_L + 0.3, y + 0.24, 0.47, 0.47, [[T(str(i + 1), size=SIZE_LABEL, bold=True, color="FFFFFF")]],
                 align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        add_text(s, MARGIN_L + 1.05, y, 7.0, 0.95, [[T(text, size=SIZE_BODY + 4, color=TEXT_ON_NAVY)]], anchor=MSO_ANCHOR.MIDDLE)
        y += 1.15
    add_rule(s, MARGIN_L, SLIDE_W - MARGIN_R, 5.55)
    add_text(s, MARGIN_L, 5.7, CONTENT_W, 0.7, [[T("Next: ", size=SIZE_BODY + 2, bold=True, color=ACCENT),
                                                 T("finish annotation, run REPaL on arXiv.", size=SIZE_BODY + 2, color=TEXT_ON_NAVY)]],
             anchor=MSO_ANCHOR.MIDDLE)
    set_notes(s, timing("4:50-5:00") + "\n" + notes["4:50-5:00"])

    # 10 --- backup
    s = add_content_slide(prs, "Backup — verified facts", 10)
    add_rect(s, 7.6, MARGIN_T + 0.12, 5.13, 0.46, BG_WHITE, line=ACCENT, rounded=True, line_w=1.25)
    add_text(s, 7.6, MARGIN_T + 0.12, 5.13, 0.46, [[T("NOT FOR THE 5-MINUTE RECORDING", size=SIZE_LABEL, bold=True, color=ACCENT)]],
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    facts = [("Local Qwen: ", "credits ran out; SemEval and NYT used Qwen2.5-32B. Qwen3-32B on SemEval: 25.1 initial, 19.6 follow-up."),
             ("Archived GPT-4o SemEval run: ", "35.7 initial, stopped when credits ran out. Single runs: only a hint."),
             ("Runs: ", "26 finished without errors; nyt_qwen3 was not run, on purpose."),
             ("Low F1 (19) next to P (45), R (20): ", "the paper averages P, R and F1 over test iterations."),
             ("SemEval hypothesis (untested): ", "model-written entities ~4\u20135 tokens; SemEval's are single words."),
             ("Pool size: ", "paper uses 10,000 unlabelled per group. My 10k run (71.6 / 68.1) mixes GPT-4o seeds, Qwen follow-up."),
             ("Group sizes (paper): ", "5 groups of 14 FewRel relations, 3 groups of 15 WikiZSL relations."),
             ("Not done yet: ", "finish annotation, REPaL on the arXiv set, LLM-as-a-judge.")]
    y = CONTENT_TOP - 0.05
    for lead, rest in facts:
        add_rect(s, MARGIN_L, y + 0.12, 0.1, 0.1, ACCENT)
        add_text(s, MARGIN_L + 0.3, y, CONTENT_W - 0.3, 0.6, [[T(lead, size=SIZE_LABEL, bold=True), T(rest, size=SIZE_LABEL, color=MUTED_ON_WHITE)]],
                 spacing=1.0)
        y += 0.6
    set_notes(s, "TIMING: backup — not for the 5-minute recording\n" + notes["ifasked"])


# ----------------------------------------------------------------------------- filled transcript + self-check
SECTION_ORDER = ["0:00-0:30", "0:30-1:15", "1:15-2:45", "2:45-3:30", "3:30-4:20", "4:20-4:50", "4:50-5:00"]
SECTION_TITLES = {"0:00-0:30": "Introduction and why this paper", "0:30-1:15": "The paper's datasets",
                  "1:15-2:45": "Architecture, code, and a run", "2:45-3:30": "Replication status", "3:30-4:20": "New datasets",
                  "4:20-4:50": "Building my own dataset: progress", "4:50-5:00": "Wrap-up"}
FILLED_TRANSCRIPT = os.path.join(ROOT, "2026-10-10-video-transcript-v3-filled.md")


def write_filled_transcript(notes):
    """Clean reading copy: the v3 spoken sections with the [FILL] values filled in (v3 itself is not modified)."""
    out = ["# Video transcript v3, values filled in (reading copy)", "",
           "Generated by `update_video/build_pptx.py` from `2026-10-10-video-transcript-v3.md`. Only the four blanks changed (and the now-resolved 'if you have labelled none' instruction was removed);",
           "the optional lines in [square brackets] are left for you to decide. The same text is in the slides' speaker notes.", ""]
    for k in SECTION_ORDER:
        out += [f"## {k}  {SECTION_TITLES[k]}", notes[k], ""]
    open(FILLED_TRANSCRIPT, "w", encoding="utf-8").write("\n".join(out))


def verify(prs, notes, raw):
    import difflib
    ok_all = True

    def check(label, cond, detail=""):
        nonlocal ok_all
        ok_all &= bool(cond)
        print(("PASS " if cond else "FAIL ") + label + (f"  [{detail}]" if detail else ""))

    slides = list(prs.slides)
    body = lambda n: slides[n - 1].notes_slide.notes_text_frame.text.split("\n", 1)[1]
    check("slide count is 10", len(slides) == 10, str(len(slides)))
    for i, s in enumerate(slides, 1):
        t = [sh.text_frame.text for sh in s.shapes if sh.has_text_frame and sh.text_frame.text.strip()]
        print(f"  slide {i:2d}: {t[0] if t else '?'}")

    # notes == filled transcript sections; and show every line that differs from the v3 text
    for n, key in {2: "0:00-0:30", 3: "0:30-1:15", 6: "2:45-3:30", 7: "3:30-4:20", 8: "4:20-4:50", 9: "4:50-5:00"}.items():
        check(f"slide {n} notes == transcript section {key} (with fills)", body(n) == notes[key])
    sec = notes["1:15-2:45"]; cut = sec.index("[Terminal:")
    check("slides 4+5 notes == transcript section 1:15-2:45 (split at the terminal cue)",
          body(4) == sec[:cut].rstrip("\n") and body(5) == sec[cut:])
    check("slide 10 notes == 'If asked' list", body(10) == notes["ifasked"])
    print("  --- lines that differ from the v3 transcript (the only edits made to the spoken text) ---")
    for k in SECTION_ORDER:
        for d in difflib.unified_diff(raw[k].split("\n"), notes[k].split("\n"), lineterm="", n=0):
            if d[:1] in "+-" and d[:3] not in ("+++", "---"):
                print(f"  [{k}] {d[:170]}")

    # no placeholders left anywhere
    left = [(i, sh.text_frame.text) for i, s in enumerate(slides, 1) for sh in s.shapes if sh.has_text_frame and "[FILL" in sh.text_frame.text]
    left += [(i, "notes") for i, s in enumerate(slides, 1) if "[FILL" in s.notes_slide.notes_text_frame.text]
    check("no [FILL] left on any slide or in any notes", not left, str(left))
    texts = {i: " ".join(sh.text_frame.text for sh in s.shapes if sh.has_text_frame) for i, s in enumerate(slides, 1)}
    check("slide 6 shows the environment", all(x in texts[6] for x in ("RTX 5090", "Python 3.12", "PyTorch 2.11")))
    check("slide 7 shows NYT 2,500 sentences / 25 relations and no SemEval example",
          "2,500" in texts[7] and "25 relations" in texts[7] and "divorce" not in texts[7])
    check("slide 8 shows 0 / 100", "0 / 100" in texts[8])
    check("slide 9 says ready to label", "ready to label" in texts[9])

    # nothing sensitive on slides, min font size
    bad = re.compile(r"https?://|www\.|github\.com|\b\d{1,3}(\.\d{1,3}){3}\b|\btoken\b|OPEN_BUTTON", re.I)
    leaks, small = [], []
    for i, s in enumerate(slides, 1):
        for sh in s.shapes:
            if sh.has_text_frame:
                if bad.search(sh.text_frame.text):
                    leaks.append((i, sh.text_frame.text[:40]))
                for p in sh.text_frame.paragraphs:
                    for r in p.runs:
                        if r.font.size and r.font.size.pt < 16 and r.text.strip():
                            small.append((i, r.text[:20], r.font.size.pt))
    check("no URL / IP / token text on any slide", not leaks, str(leaks))
    check("no text below 16 pt on slides", not small, str(small[:3]))

    words = sum(len(ln.split()) for sl in slides[1:9] for ln in sl.notes_slide.notes_text_frame.text.split("\n")
                if ln.strip() and not ln.startswith("[") and not ln.startswith("TIMING:"))
    print(f"  spoken words in notes (slides 2-9): {words}")
    print("ALL CHECKS PASSED" if ok_all else "SOME CHECKS FAILED")
    return ok_all


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--refresh-chart", action="store_true")
    args = ap.parse_args()
    raw = parse_transcript(TRANSCRIPT)
    notes = {k: apply_fills(v) for k, v in raw.items()}
    add_bar_chart(CHART_PNG, refresh=args.refresh_chart)
    prs = Presentation()
    prs.slide_width, prs.slide_height = I(SLIDE_W), I(SLIDE_H)
    build(prs, notes)
    prs.save(OUT_PPTX)
    print("wrote", OUT_PPTX)
    write_filled_transcript(notes)
    sys.exit(0 if verify(Presentation(OUT_PPTX), notes, raw) else 1)


if __name__ == "__main__":
    main()
