// Builds REPaL_Run_Report.docx (A4). Run: node build_report.js <out.docx>
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell, WidthType, ShadingType,
  AlignmentType, BorderStyle, ImageRun, LevelFormat, Footer, PageNumber, TableLayoutType, ExternalHyperlink, LineRuleType,
} = require("docx");

const OUT = process.argv[2] || "REPaL_Run_Report.docx";
const ACCENT = "0F6B63", MUTED = "5B6765", RULE = "D5DBD9", HEAD_FILL = "E7EEEC", GOOD = "1F7A3F", BAD = "B03A2E";
const CONTENT_W = 9638; // A4 width 11906 - 2 x 1134 margins

// "text **bold** text" -> TextRuns; `code` -> monospace
function runs(text, opts = {}) {
  const out = [];
  let last = 0;
  for (const m of text.matchAll(/(\*\*[^*]+\*\*|`[^`]+`)/g)) {
    if (m.index > last) out.push(new TextRun({ text: text.slice(last, m.index), ...opts }));
    const t = m[0];
    if (t.startsWith("**")) out.push(new TextRun({ text: t.slice(2, -2), bold: true, ...opts }));
    else out.push(new TextRun({ text: t.slice(1, -1), font: "Consolas", ...opts, size: (opts.size || 21) - 2 }));
    last = m.index + t.length;
  }
  if (last < text.length) out.push(new TextRun({ text: text.slice(last), ...opts }));
  return out;
}
const p = (text, o = {}) => new Paragraph({ children: runs(text, o.run || {}), spacing: { after: 120, ...(o.spacing || {}) }, alignment: o.align });
const note = (text) => p(text, { run: { size: 18, color: MUTED } });
const h1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] });
const h2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] });
const bullet = (text) => new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: runs(text), spacing: { after: 50 } });

function table(headers, rows, widths, { numeric = [], colors = {} } = {}) {
  const sum = widths.reduce((a, b) => a + b, 0);
  if (sum !== CONTENT_W) widths = widths.map((w, i) => (i === widths.length - 1 ? w + CONTENT_W - sum : w));
  const border = { style: BorderStyle.SINGLE, size: 4, color: RULE };
  const borders = { top: border, bottom: border, left: border, right: border };
  const cell = (text, i, header, rowIdx) => new TableCell({
    width: { size: widths[i], type: WidthType.DXA },
    borders,
    shading: header ? { type: ShadingType.CLEAR, color: "auto", fill: HEAD_FILL } : undefined,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [new Paragraph({
      alignment: numeric.includes(i) ? AlignmentType.RIGHT : AlignmentType.LEFT,
      children: runs(String(text), header ? { bold: true, size: 17, color: MUTED } : { size: 19, color: colors[`${rowIdx},${i}`] }),
    })],
  });
  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: widths, layout: TableLayoutType.FIXED,
    rows: [
      new TableRow({ tableHeader: true, children: headers.map((h, i) => cell(h, i, true)) }),
      ...rows.map((r, ri) => new TableRow({ cantSplit: true, children: r.map((c, i) => cell(c, i, false, ri)) })),
    ],
  });
}
function image(file, wPx, hPx, caption) {
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 80, after: 40, line: 240, lineRule: LineRuleType.AUTO }, keepNext: true,
      children: [new ImageRun({ type: "png", data: fs.readFileSync(file), transformation: { width: wPx, height: hPx },
        altText: { title: caption, description: caption, name: file } })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 160 }, children: [new TextRun({ text: caption, italics: true, size: 17, color: MUTED })] }),
  ];
}
// const link = (url, text) => new Paragraph({ spacing: { after: 60 }, children: [new ExternalHyperlink({ link: url, children: [new TextRun({ text, style: "Hyperlink", size: 19 })] })] });

const children = [
  // ---------- title ----------
  new Paragraph({ spacing: { after: 160 }, children: [new TextRun({ text: "RUN REPORT · 6–8 OCT 2026 · VAST.AI, 2× RTX 5090", size: 16, color: ACCENT, bold: true, characterSpacing: 20 })] }),
  new Paragraph({ heading: HeadingLevel.TITLE, children: [new TextRun("REPaL Run Report")] }),
  p("What we ran, what came out, what broke and how it got fixed. REPaL (EMNLP 2024) learns a relation extractor from nothing but a written definition of each relation: an LLM writes example sentences, a small RoBERTa model is trained on them, then the model's own guesses are fed back to the LLM for a second round.", { run: { color: MUTED } }),
  note("21 runs · 4 datasets · ~50 GPU-hours · LLMs: GPT-4o, then Qwen2.5-32B (local) · small model: roberta-large-mnli"),
  table(["FewRel F1 after feedback", "Wiki-ZSL F1 after feedback", "SemEval initial F1", "NYT initial F1 (new)"],
    [["**69.6**  (paper 74.6)", "**46.0**  (paper 47.8)", "**35.7 → 19.0**  (GPT-4o → Qwen)", "**48.3**  (Qwen)"]],
    [2410, 2410, 2409, 2409]),

  // ---------- 1 ----------
  h1("1. Summary"),
  bullet("**Reproduction:** FewRel lands about 5 F1 points below the paper, with the same +4.7-point gain from the feedback round that the paper reports. Wiki-ZSL lands close to the paper (46.0 vs 47.8), but there the feedback round did not help."),
  bullet("**Two new datasets** were built in REPaL's format: SemEval-2010 Task 8 (17 directed relations) and FewRel 2.0's NYT news set (25 relations)."),
  bullet("**OpenAI credits ran out** partway through, so the new datasets were finished with a local open model (Qwen2.5-32B-Instruct-AWQ via vLLM). Same pipeline, no API key."),
  bullet("**The generator LLM matters a lot.** On SemEval's first stage, swapping GPT-4o for Qwen nearly halved F1 (35.7 → 19.0). The feedback round then recovered most of it (19.0 → 31.0)."),
  bullet("**Feedback trades recall for precision** on every dataset. Whether F1 goes up depends on which way that balance tips."),
  bullet("Along the way we fixed 2 bugs in the original code, a results-file race between parallel runs, and a lot of infrastructure: a damaged disk cache, a missing spaCy model, PyPI timeouts and GPU memory limits."),

  // ---------- 2 ----------
  h1("2. The datasets"),
  p("Every dataset is in \"DefOn\" (definition-only) form. Each split has a set of test relations, each with a written definition. For each relation, the model must find its sentences among all the test sentences, so the other test relations act as negatives. The first 50 sentences of each relation are held back unscored."),
  table(["Dataset", "Text", "Splits", "Test rels", "Test sents", "Pool", "Definitions from", "LLM"],
    [
      ["**DefOn-FewRel**", "Wikipedia", "5", "14", "~9,800", "100,000", "Wikidata, edited by authors", "GPT-4o (cached)"],
      ["**DefOn-Wiki-ZSL**", "Wikipedia", "3", "15", "12.1–12.9k", "100,000", "Wikidata, edited by authors", "GPT-4o (cached)"],
      ["**SemEval-2010 T8** (new)", "Web / general", "1", "17", "8,851", "8,851 *", "Task paper, verbatim", "GPT-4o, then Qwen"],
      ["**FewRel 2.0 NYT** (new)", "News", "1", "25", "2,500", "2,500 *", "Authors' prompts (18) + Wikidata (7)", "Qwen"],
    ],
    [1550, 1250, 760, 760, 1080, 1050, 1850, 1338], { numeric: [2, 3, 4, 5] }),
  note("* No separate unlabeled corpus exists, so the pool is the test sentences with all labels removed. The paper's own FewRel split already overlaps this way: 4,281 of 9,798 test sentences are also in its pool."),

  h2("FewRel and Wiki-ZSL (the paper's datasets)"),
  p("Both are Wikipedia sentences labelled with Wikidata relations (e.g. employer, mother, member of sports team). We used the authors' released data, including their cached GPT-4o outputs, so these runs needed no API calls. One mismatch: the released unlabeled pools hold **100,000** sentences per split, while the EMNLP paper text says 10,000. The paper's earlier arXiv v1 is internally inconsistent on this (its table says 100k, its text 10k)."),
  h2("SemEval-2010 Task 8 (new)"),
  p("A classic benchmark of nine general relations between nouns (Cause-Effect, Component-Whole, Content-Container, Entity-Origin, Entity-Destination, Instrument-Agency, Member-Collection, Message-Topic, Product-Producer). Each comes in both directions, which makes it a hard test of definitions: \"the burst was caused by pressure\" is Cause-Effect(e2,e1), not (e1,e2). Source: the official FewRel repo, already in REPaL's format. It's the full SemEval set minus \"Other\" and two rare instances. Definitions are the task paper's own sentences, wrapped in REPaL's `<ENT0>/<ENT1>` template. I checked the direction mapping against real sentences for every relation."),
  h2("FewRel 2.0 NYT (new)"),
  p("New York Times sentences with 25 Wikidata relations, 100 sentences each. It's a news-domain test with real Wikidata definitions. 18 relations also appear in FewRel/Wiki-ZSL, so they reuse the authors' exact prompts. That isn't leakage, because REPaL never trains on labelled data. I wrote the other 7 prompts (parent taxon, ethnic group, director of photography, stock exchange, cause of death, parent organization, present in work) from Wikidata's descriptions. Only 50 sentences per relation get scored, so per-relation numbers are noisy."),
  h2("Considered but not used"),
  p("**FewRel 2.0 PubMed** (biomedical): no official definitions exist for all 10 of its relations, and it's small. **Re-DocRED** (MIT licence, large): document-level, so it needs real conversion work. It's the best option for a larger follow-up. **Re-TACRED** was used in the paper's first arXiv version but needs an LDC licence."),

  // ---------- 3 ----------
  h1("3. Results"),
  p("Scores are the repo's official per-run P/R/F1 (×100). \"Initial\" is training on 15 positive + 15 negative LLM-written seeds per relation. \"Follow-up\" adds one feedback round that mines the model's own predictions and has the LLM write 15+15 more."),
  ...image("chart_main.png", 620, 305, "Figure 1. F1 by dataset. FewRel and Wiki-ZSL are means over splits (5 and 3); the marker is the paper's final (follow-up) F1."),
  table(["Dataset", "LLM", "Stage", "P", "R", "F1", "± std", "Paper F1"],
    [
      ["FewRel", "GPT-4o", "Initial", "67.0", "75.5", "64.9", "1.1", "70.0 †"],
      ["", "", "Follow-up", "79.4", "68.8", "**69.6**  (+4.7)", "3.3", "74.6"],
      ["Wiki-ZSL", "GPT-4o", "Initial", "64.7", "51.4", "49.2", "2.3", "n/a"],
      ["", "", "Follow-up", "68.7", "42.3", "**46.0**  (−3.2)", "5.0", "47.8"],
      ["SemEval", "GPT-4o", "Initial", "57.2", "34.6", "35.7", "–", "–"],
      ["", "Qwen2.5-32B", "Initial", "45.4", "20.4", "19.0", "–", "–"],
      ["", "", "Follow-up", "45.5", "35.9", "**31.0**  (+12.0)", "–", "–"],
      ["NYT", "Qwen2.5-32B", "Initial", "51.9", "57.0", "48.3", "–", "–"],
      ["", "", "Follow-up", "68.7", "45.7", "**47.1**  (−1.2)", "–", "–"],
    ],
    [1150, 1650, 1150, 850, 850, 1700, 850, 1438], { numeric: [3, 4, 5, 6, 7],
      colors: { "1,5": GOOD, "3,5": BAD, "6,5": GOOD, "8,5": BAD } }),
  note("Paper numbers: arXiv v2 = EMNLP 2024 version, Table 1 (REPaL w/ GPT-4o: FewRel P 78.86 / R 77.28 / F1 74.61; Wiki-ZSL 68.98 / 47.63 / 47.80). † FewRel \"iteration 1\" from the paper's Table 4. I only had this one from a summary of the page, not verbatim. The SemEval GPT-4o follow-up never ran because OpenAI credits ran out mid-stage."),

  h2("Per split (GPT-4o datasets)"),
  table(["Split", "FewRel initial", "FewRel follow-up", "Δ", "Wiki-ZSL initial", "Wiki-ZSL follow-up", "Δ"],
    [
      ["1", "65.5", "68.6", "+3.1", "51.2", "51.3", "+0.1"],
      ["2", "65.4", "75.6", "+10.2", "45.9", "39.3", "−6.6"],
      ["3", "64.3", "65.5", "+1.2", "50.3", "47.3", "−3.0"],
      ["4", "66.2", "68.8", "+2.6", "–", "–", "–"],
      ["5", "63.0", "69.6", "+6.7", "–", "–", "–"],
    ],
    [900, 1450, 1500, 1000, 1550, 1700, 1538], { numeric: [1, 2, 3, 4, 5, 6],
      colors: { "0,3": GOOD, "1,3": GOOD, "2,3": GOOD, "3,3": GOOD, "4,3": GOOD, "1,6": BAD, "2,6": BAD } }),
  p("FewRel improves on every split. On Wiki-ZSL, feedback raised precision but cut recall further, especially on split 2 (recall 40.9 → 31.2).", { spacing: { before: 120 } }),

  h2("SemEval: GPT-4o vs Qwen, per relation"),
  ...image("chart_semeval.png", 470, 463, "Figure 2. SemEval per-relation F1 as last logged during each run (useful for comparing relations; the stage scores above are the official ones)."),
  bullet("GPT-4o seeds beat Qwen's initial seeds on 14 of 17 relations (one tie). Qwen's examples were often fluent but tagged the wrong pair (e.g. two effects instead of cause and effect), and 17% of its outputs were rejected as malformed."),
  bullet("Qwen's feedback round helped most where the first model had found something to learn from (Product-Producer, Entity-Destination, Entity-Origin)."),
  bullet("**Member-Collection** and **Cause-Effect(e1,e2)** stayed near zero with Qwen. The second had zero confident predictions after the first stage, which is what exposed the code bug in section 4."),

  h2("NYT: what feedback did per relation"),
  ...image("chart_nyt.png", 470, 448, "Figure 3. NYT per-relation F1 (last logged), Qwen2.5-32B as generator. Only 50 scored sentences per relation, so single-relation swings are noisy."),
  p("Feedback improved 15 of 25 NYT relations, sometimes a lot (position played +57, industry +42, member of sports team +32). It also broke a few that had been fine (parent taxon −57, voice type −40, ethnic group −24). Overall F1 is flat (48.3 → 47.1): precision rose 17 points and recall fell 11. That's the same pattern as Wiki-ZSL."),

  h2("Run times"),
  table(["Dataset", "Initial (h)", "Follow-up (h)", "Total (h)", "Notes"],
    [
      ["FewRel ×5", "2.7–3.3", "1.6", "23.4", "Run one after another"],
      ["Wiki-ZSL ×3", "3.0–4.2", "2.3–2.5", "18.3", "Largest test sets; splits 2 and 3 ran in parallel"],
      ["SemEval (GPT-4o)", "2.1", "–", "2.1", "Follow-up stopped: no credits"],
      ["SemEval (Qwen)", "2.2", "2.0", "4.2", "LLM on GPU 0, training on GPU 1"],
      ["NYT (Qwen)", "0.9", "1.3", "2.3", "Smallest pool"],
    ],
    [1800, 1250, 1400, 1100, 4088], { numeric: [1, 2, 3] }),

  // ---------- 4 ----------
  h1("4. Challenges and how they were solved"),
  table(["Problem", "Cause", "Fix"],
    [
      ["All Wiki-ZSL runs failed in 9 s", "Corrupted cached tensors; later \"stale file handle\" errors showed damaged files in both HF model caches on the instance disk", "Re-downloaded the model to a fresh cache (`/root/hf_fresh`), scanned data dirs (clean), resumed. Split 1 kept its 7 finished relations"],
      ["Jobs died with \"No module named transformers\"", "Instance was rebuilt; Python packages gone", "Reinstalled `requirements.txt`. `uv` hung, so I switched to `pip`. torch (cu128, needed for RTX 5090) untouched"],
      ["Wiki-ZSL split 2 and SemEval vanished from the results tables", "Two parallel drivers each rewrote `summary.csv` from a stale in-memory copy; last writer won", "File lock + re-read-before-write in `run_experiments.py`; rebuilt rows from per-run `metrics.json` (no data lost)"],
      ["SemEval follow-up: Can't find model 'en_core_web_trf'", "The feedback step needs a spaCy model the cached runs never used", "Installed v3.7.3 from spaCy's GitHub release. The PyPI package of that name is a placeholder (v999.9.9), not the model"],
      ["OpenAI 429 insufficient_quota", "Account credits ran out mid-follow-up", "Switched to a local LLM (below). The API key was pasted in chat, so it should be rotated"],
      ["vLLM wouldn't install", "Read timeouts from PyPI's file server (also the real reason `uv` hung)", "Separate venv (`/venv/vllm`, its own torch 2.13/cu130), pip with long timeout and retries"],
      ["Couldn't train NYT next to the LLM on GPU 0", "The 32B model needs ~25 GB; RoBERTa-large training at the paper's batch size needs more than the ~6.7 GB left", "LLM keeps GPU 0, training runs one job at a time on GPU 1 (auto-queued)"],
      ["Follow-up crash: Sample larger than population", "**Original-code bug:** the negative-feedback step samples 30 confident predictions and assumes ≥30 exist. The authors had patched the positive step (`max(40, …)`) but not this one", "Applied the authors' own floor to the negative step; capped all sampling at what's available; also fixed a `range(list)` bug in an unused branch"],
      ["Dashboard showed \"45 h to finish\"", "That was time since the first run (2 days); the ETA itself averaged all runs × count; start times never parsed (header read too short)", "Relabelled, per-run ETA using each job's own pace, fixed start-time parsing"],
      ["Dashboard restarts didn't take effect", "Supervisor stopped the wrapper script but the Python child kept the port", "`stopasgroup/killasgroup` in the service config"],
    ],
    [2500, 3500, 3638]),

  // ---------- 5 ----------
  h1("5. What was changed"),
  table(["Where", "Change"],
    [
      ["`src/trainer.py`", "Negative-feedback sampling fix (floor of 40, sample ≤ available), `range(len(…))` fix"],
      ["`src/model.py`", "Rate-limit entry for local `Qwen/` models (otherwise throttled to 10k tokens/min)"],
      ["`run_experiments.py`", "Registers `semeval` and `nyt`; locked summary writes; `gpu_shared` batch profile"],
      ["`tools/build_semeval_defon.py`, `tools/build_nyt_defon.py`, `tools/run_local_llm.sh`", "Rebuild the two new datasets from the FewRel repo files (design choices documented in the docstrings); run any dataset against the local LLM (`OPENAI_BASE_URL`, model, GPU, profile)"],
      ["`data/semeval_1`, `data/nyt_1`", "The new datasets. GPT-4o SemEval run archived under `results/archive/` and `data/archive/`"],
      ["Instance services", "`repal-dashboard` (v0.3.1: smoke tests removed, parallel jobs, new datasets, real ETA) and `qwen-llm` (vLLM, GPU 0, local-only)"],
      ["Environment", "Reinstalled requirements, `en_core_web_trf`, separate `/venv/vllm`; clean HF cache at `/root/hf_fresh`"],
    ],
    [3300, 6338]),

  // ---------- 6 ----------
  h1("6. Conclusions"),
  bullet("**The reproduction is reasonable but not exact.** FewRel is 5 points under the paper at both stages, so the gap is in the setup, not the feedback step. The one concrete difference I found is the unlabeled pool size (100k released vs 10k described in the paper). I haven't tested it, but it's a cheap thing to try first."),
  bullet("**Feedback is a precision tool.** It raised precision everywhere (FewRel +12, NYT +17) and lowered recall almost everywhere. It pays off when the first model's recall is high (FewRel) and hurts when recall is already low (Wiki-ZSL, NYT)."),
  bullet("**The LLM is the ceiling.** The same pipeline lost almost half its first-stage F1 on SemEval when GPT-4o was swapped for a local 32B model. The local route works and costs nothing per call, but GPT-4o numbers and Qwen numbers shouldn't be mixed."),
  bullet("**Directional relations are hard from definitions alone.** On SemEval, mirrored pairs (X(e1,e2) vs X(e2,e1)) often scored very differently, and some stayed near zero with both LLMs."),
  bullet("**NYT works with REPaL out of the box.** At 48 F1 it sits at Wiki-ZSL's level, but with one split and 50 sentences per relation, treat it as a first look."),
  h2("Worth trying next"),
  bullet("Re-run one FewRel split with a 10k unlabeled pool to test the gap to the paper."),
  bullet("Finish SemEval and NYT with GPT-4o (once credits are back) for a clean LLM comparison. The GPT-4o SemEval first stage is already archived."),
  bullet("Try a stronger local model (e.g. Qwen3-32B with \"thinking\" disabled) to see how much of the GPT-4o gap closes."),
  bullet("Build Re-DocRED for a large, realistic test with a big natural unlabeled pool."),

  h2("Corrections to things I told you during the runs"),
  note("I first reported Wiki-ZSL as 51.4 ± 8.1 (initial) and 42.3 ± 8.6 (follow-up). Those were recall columns, misread when I cut the CSV. The correct F1 is 49.2 ± 2.3 and 46.0 ± 5.0, as above. My earlier SemEval follow-up ETA (09:15–09:45) was also too early. It finished at 11:01 UTC."),

  new Paragraph({ spacing: { before: 60, after: 0 }, children: [
    new TextRun({ text: "Sources: ", bold: true, size: 17, color: MUTED }),
    new ExternalHyperlink({ link: "https://arxiv.org/abs/2402.11142", children: [new TextRun({ text: "REPaL paper (arXiv 2402.11142 v1/v2)", style: "Hyperlink", size: 17 })] }),
    new TextRun({ text: " · ", size: 17, color: MUTED }),
    new ExternalHyperlink({ link: "https://arxiv.org/html/1911.10422v1", children: [new TextRun({ text: "SemEval-2010 Task 8 paper", style: "Hyperlink", size: 17 })] }),
    new TextRun({ text: " · ", size: 17, color: MUTED }),
    new ExternalHyperlink({ link: "https://github.com/thunlp/FewRel", children: [new TextRun({ text: "FewRel / FewRel 2.0 data", style: "Hyperlink", size: 17 })] }),
    new TextRun({ text: " · ", size: 17, color: MUTED }),
    new ExternalHyperlink({ link: "https://huggingface.co/Qwen/Qwen2.5-32B-Instruct-AWQ", children: [new TextRun({ text: "Qwen2.5-32B-Instruct-AWQ", style: "Hyperlink", size: 17 })] }),
    new TextRun({ text: ". Result numbers come from results/summary.csv and the per-run logs on the instance.", size: 17, color: MUTED }),
  ] }),
];

const doc = new Document({
  creator: "Claude", title: "REPaL Run Report", description: "REPaL reproduction and extension runs, 6–8 Oct 2026",
  styles: {
    default: { document: { run: { font: "Calibri", size: 21, color: "1D2524" }, paragraph: { spacing: { line: 276, lineRule: LineRuleType.AUTO } } } },
    paragraphStyles: [
      { id: "Title", name: "Title", basedOn: "Normal", next: "Normal", run: { font: "Cambria", size: 44, bold: true, color: "1D2524" }, paragraph: { spacing: { after: 120 } } },
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: "Cambria", size: 30, bold: true, color: ACCENT },
        paragraph: { spacing: { before: 260, after: 100 }, keepNext: true, outlineLevel: 0, border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: RULE, space: 4 } } } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: "Calibri", size: 23, bold: true, color: "1D2524" },
        paragraph: { spacing: { before: 180, after: 70 }, keepNext: true, outlineLevel: 1 } },
    ],
  },
  numbering: { config: [{ reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
    style: { paragraph: { indent: { left: 360, hanging: 240 } } } }] }] },
  sections: [{
    properties: { page: { margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.RIGHT,
      children: [new TextRun({ text: "REPaL Run Report · page ", size: 16, color: MUTED }), new TextRun({ children: [PageNumber.CURRENT], size: 16, color: MUTED })] })] }) },
    children,
  }],
});
Packer.toBuffer(doc).then((b) => { fs.writeFileSync(OUT, b); console.log("wrote", OUT, b.length, "bytes"); });
