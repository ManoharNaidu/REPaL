#!/usr/bin/env python3
"""Turn corpus/abstracts.jsonl into (1) corpus/sentences.jsonl and (2) corpus/distant.json, REPaL's unlabeled-corpus format.

Sentence splitting: spaCy 3.7 blank English pipeline + rule-based sentencizer (no model download needed).
Entity candidates (no NER model is available for scientific text, so this is a deliberately simple, noisy
heuristic): acronyms (BERT, BLEU), CamelCase / letter+digit names (ImageNet, GPT-4, F1), capitalised words
that are not sentence-initial (Transformer, Wikipedia), a small list of metric words (accuracy, F1, ...) and
numeric scores (84.5%). Adjacent candidate tokens are merged into one mention.
Pairs: for each sentence with >= 2 mentions, mention pairs in textual order (head = earlier mention,
tail = later mention), nearest pairs first, at most MAX_PAIRS per sentence.

distant.json schema (identical to data/semeval_1/distant.json):
  {"UNLABELED": [{"tokens": [...], "h": [text, text, [[token idx, ...]]], "t": [text, text, [[token idx, ...]]]}, ...]}
usage: python arxiv_re/preprocess_abstracts.py
"""
import json, os, re, statistics
import spacy

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "corpus")
MIN_TOK, MAX_TOK, MAX_PAIRS = 8, 60, 6
METRICS = {"accuracy", "precision", "recall", "f1", "f1-score", "bleu", "rouge", "perplexity", "auc", "map", "mrr", "ndcg",
           "fid", "psnr", "ssim", "miou", "wer", "cer", "latency", "throughput", "pass@1", "exact", "em"}
STOP_CAP = {"We", "The", "This", "These", "In", "Our", "It", "To", "However", "Moreover", "Furthermore", "Specifically",
            "Additionally", "For", "On", "By", "With", "While", "Although", "Despite", "Recent", "Existing"}
HEAD_NOUNS = {"model", "models", "method", "methods", "approach", "framework", "dataset", "datasets", "benchmark", "benchmarks",
              "algorithm", "algorithms", "baseline", "baselines", "network", "networks", "architecture", "technique", "system", "corpus"}
MOD_STOP = {"a", "an", "the", "of", "in", "we", "our", "this", "that", "these", "those", "and", "or", "to", "for", "with", "by", "on",
            "is", "are", "was", "were", "be", "as", "from", "than", "which", "its", "their", "such", "new", "novel", "proposed", "existing",
            "several", "many", "other", "both", "all", "each", "using", "use", "uses", "show", "that"}
camel = re.compile(r"^(?=.*[a-z])(?=.*[A-Z]).*[a-z][A-Z]|^[A-Z][a-z]+[A-Z]")
alnum = re.compile(r"^[A-Za-z]+[-]?\d+(\.\d+)?[A-Za-z]*$|^\d+[A-Za-z]+$")
num = re.compile(r"^\d+(\.\d+)?$")


def is_cand(tok, i):
    t = tok.text
    if not t.strip() or tok.is_punct:
        return False
    if t.isupper() and len(t) >= 2 and t.isalpha():
        return True
    if camel.search(t) or alnum.match(t):
        return True
    if t.lower() in METRICS:
        return True
    if i > 0 and t[0].isupper() and t.isalpha() and t not in STOP_CAP and len(t) > 2:
        return True
    return False


def mentions(doc):
    toks = list(doc)
    flags = [is_cand(t, i) for i, t in enumerate(toks)]
    for i, tk in enumerate(toks):                         # generic head noun + up to 3 modifiers: "bilingual training dataset"
        if tk.text.lower() in HEAD_NOUNS and i > 0:
            flags[i] = True; k = i - 1
            while k >= 0 and i - k <= 3 and toks[k].text.lower() not in MOD_STOP and not toks[k].is_punct and not toks[k].like_num:
                flags[k] = True; k -= 1
    for i in range(len(toks) - 1):                        # numeric score: "84.5" followed by "%"
        if num.match(toks[i].text) and toks[i + 1].text == "%":
            flags[i] = flags[i + 1] = True
    out, i = [], 0
    while i < len(toks):
        if flags[i]:
            j = i
            while j + 1 < len(toks) and (flags[j + 1] or (toks[j + 1].text == "-" and j + 2 < len(toks) and flags[j + 2])):
                j += 1
            out.append(list(range(i, j + 1))); i = j + 1
        else:
            i += 1
    return out


def main():
    nlp = spacy.blank("en"); nlp.add_pipe("sentencizer")
    absts = [json.loads(l) for l in open(os.path.join(DATA, "abstracts.jsonl"), encoding="utf-8")]
    sents, dist, n_all, n_len = [], [], 0, 0
    for a in absts:
        for k, s in enumerate(nlp(a["abstract"]).sents):
            n_all += 1
            doc = s.as_doc()
            if not (MIN_TOK <= len(doc) <= MAX_TOK):
                continue
            n_len += 1
            ms = mentions(doc)
            sid = f'{a["arxiv_id"]}_s{k}'
            toks = [t.text for t in doc]
            sents.append(dict(sent_id=sid, arxiv_id=a["arxiv_id"], category=a["category"], date=a["date"], sentence=doc.text,
                              tokens=toks, mentions=[[" ".join(toks[i] for i in m), m] for m in ms]))
            if len(ms) >= 2:
                pairs = sorted(((x, y) for ix, x in enumerate(ms) for y in ms[ix + 1:]), key=lambda p: p[1][0] - p[0][-1])
                pairs = [(h, t) for h, t in pairs if not (t[0] - h[-1] == 2 and toks[h[-1] + 1] == "(")][:MAX_PAIRS]   # drop "Name (ACRONYM)", then cap
                for h, t in pairs:
                    ht, tt = " ".join(toks[i] for i in h), " ".join(toks[i] for i in t)
                    dist.append({"tokens": toks, "h": [ht, ht, [h]], "t": [tt, tt, [t]]})
    with open(os.path.join(DATA, "sentences.jsonl"), "w", encoding="utf-8") as f:
        for s in sents:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")
    json.dump({"UNLABELED": dist}, open(os.path.join(DATA, "distant.json"), "w", encoding="utf-8"), ensure_ascii=False)
    lens = [len(s["tokens"]) for s in sents]
    two = [s for s in sents if len(s["mentions"]) >= 2]
    stats = dict(
        abstracts=len(absts), sentences_total=n_all, sentences_kept_len=n_len,
        sentences_with_2plus_mentions=len(two), candidate_pairs=len(dist),
        tokens_per_sentence_mean=round(statistics.mean(lens), 1), tokens_per_sentence_median=statistics.median(lens),
        tokens_per_sentence_min=min(lens), tokens_per_sentence_max=max(lens),
        mentions_per_sentence_mean=round(statistics.mean(len(s["mentions"]) for s in sents), 2),
        abstracts_by_category={c: sum(a["category"] == c for a in absts) for c in sorted({a["category"] for a in absts})},
        date_range=[min(a["date"] for a in absts), max(a["date"] for a in absts)],
        filters=dict(min_tokens=MIN_TOK, max_tokens=MAX_TOK, max_pairs_per_sentence=MAX_PAIRS))
    json.dump(stats, open(os.path.join(DATA, "preprocess_stats.json"), "w"), indent=1)
    print(json.dumps(stats, indent=1))


if __name__ == "__main__":
    main()
