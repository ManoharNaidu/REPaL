#!/usr/bin/env python3
"""Collect arXiv abstracts via the official API (https://export.arxiv.org/api/query).

Respects the API terms of use: one request at a time, >= 3 s between requests, descriptive User-Agent.
Plan: for each category x month window (2025-01 .. 2026-09) request a few results at a seeded random
offset (so we do not just get the first submissions of each month) and keep papers whose PRIMARY category is
that category, until TARGET_PER_CAT per category. Cross-listed duplicates are removed by arXiv id.
Resumable: finished (category, window) pairs are recorded in corpus/collect_state.json and rows are appended
to corpus/abstracts.jsonl; re-running continues where it stopped.

usage: python arxiv_re/collect_abstracts.py [--per-cat 80] [--per-window 4]
"""
import argparse, json, os, random, re, sys, time, urllib.error, urllib.parse, urllib.request
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "corpus")
OUT = os.path.join(DATA, "abstracts.jsonl")
STATE = os.path.join(DATA, "collect_state.json")
CATS = ["cs.CL", "cs.LG", "cs.CV", "cs.IR", "stat.ML"]
MONTHS = [(y, m) for y in (2025, 2026) for m in range(1, 13) if (y, m) <= (2026, 9)]
UA = "COMP8240-REPaL-student-project/1.0 (academic coursework; contact: beesettim27@gmail.com)"
API = "https://export.arxiv.org/api/query"
NS = {"a": "http://www.w3.org/2005/Atom", "x": "http://arxiv.org/schemas/atom"}
MIN_GAP = 3.2   # seconds between requests (API asks for >= 3)
_last = 0.0


def fetch(url):
    """One polite GET with retry/backoff; returns bytes."""
    global _last
    for attempt in range(5):
        wait = MIN_GAP - (time.time() - _last)
        if wait > 0:
            time.sleep(wait)
        _last = time.time()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except (urllib.error.URLError, TimeoutError) as e:
            back = 10 * (attempt + 1)
            print(f"  request failed ({e}); retry in {back}s", file=sys.stderr)
            time.sleep(back)
    raise RuntimeError("arXiv API unreachable after retries")


def window_query(cat, y, m):
    nm = (y + (m == 12), 1 if m == 12 else m + 1)
    lo, hi = f"{y}{m:02d}010000", f"{nm[0]}{nm[1]:02d}010000"
    return f"cat:{cat} AND submittedDate:[{lo} TO {hi}]"


def parse(xml):
    root = ET.fromstring(xml)
    total = int(root.findtext("{http://a9.com/-/spec/opensearch/1.1/}totalResults") or 0)
    rows = []
    for e in root.findall("a:entry", NS):
        aid = re.sub(r"v\d+$", "", e.findtext("a:id", "", NS).rsplit("/abs/", 1)[-1])
        prim = e.find("x:primary_category", NS)
        rows.append(dict(
            arxiv_id=aid,
            title=" ".join(e.findtext("a:title", "", NS).split()),
            date=e.findtext("a:published", "", NS)[:10],
            category=prim.get("term") if prim is not None else None,
            categories=[c.get("term") for c in e.findall("a:category", NS)],
            abstract=" ".join(e.findtext("a:summary", "", NS).split()),
        ))
    return total, rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-cat", type=int, default=80)
    ap.add_argument("--per-window", type=int, default=4)
    a = ap.parse_args()
    os.makedirs(DATA, exist_ok=True)
    state = json.load(open(STATE)) if os.path.exists(STATE) else {"done": []}
    seen, count = set(), {c: 0 for c in CATS}
    if os.path.exists(OUT):
        for ln in open(OUT, encoding="utf-8"):
            r = json.loads(ln); seen.add(r["arxiv_id"]); count[r["category"]] = count.get(r["category"], 0) + 1
    print("resuming with", len(seen), "abstracts:", count)
    for (y, m) in MONTHS:
        for cat in CATS:
            wid = f"{cat}|{y}-{m:02d}"
            if wid in state["done"] or count.get(cat, 0) >= a.per_cat:
                continue
            q = window_query(cat, y, m)
            rng = random.Random(wid)          # deterministic offset per window -> reproducible, resumable
            # first call learns how many papers the window has, then we jump to a random offset
            url = f"{API}?search_query={urllib.parse.quote(q)}&start=0&max_results=1"
            total, _ = parse(fetch(url))
            start = rng.randrange(0, max(1, total - 12)) if total > 12 else 0
            url = (f"{API}?search_query={urllib.parse.quote(q)}&start={start}&max_results=12"
                   "&sortBy=submittedDate&sortOrder=ascending")
            _, rows = parse(fetch(url))
            kept = 0
            with open(OUT, "a", encoding="utf-8") as f:
                for r in rows:
                    if (r["category"] != cat or r["arxiv_id"] in seen or kept >= a.per_window
                            or not ("2025-01-01" <= r["date"] <= "2026-09-30") or len(r["abstract"]) < 200):
                        continue
                    f.write(json.dumps(r, ensure_ascii=False) + "\n"); seen.add(r["arxiv_id"])
                    count[cat] += 1; kept += 1
            state["done"].append(wid)
            json.dump(state, open(STATE, "w"))
            print(f"{wid}: window has {total} papers, kept {kept} | totals {count}", flush=True)
    print("DONE", len(seen), count)


if __name__ == "__main__":
    main()
