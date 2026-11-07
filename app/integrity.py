"""Content-integrity checks that need no LLM (so they cannot hallucinate):

* plagiarism(): finds stretches of the lesson copied verbatim from the fetched sources (word n-gram runs)
* scan_injection(): detects instruction-like text planted in fetched web pages (prompt injection)
"""
import re

SHINGLE = 8            # a verbatim run shorter than this is ordinary shared phrasing
MIN_FLAG_RUN = 12      # words copied in a row before a sentence is flagged
MAJOR_RUN = 25
TOTAL_MAJOR = 0.10     # share of lesson words that are verbatim source text
TOTAL_CRITICAL = 0.25


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+(?:'[a-z]+)?", text.lower())


def _prose_lines(content: str):
    """Yield (line, in_quote_block) for prose lines only (headings, tables, code, tokens skipped)."""
    in_code = False
    for line in content.splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        s = line.strip()
        if in_code or not s or s.startswith(("#", "|")) or re.fullmatch(r"\{\{video:S\d+\}\}", s):
            continue
        yield line, s.startswith(">")


_SENT_END = re.compile(r"[.!?](?:\s*\[S\d+(?:\s*,\s*S\d+)*\])*(?=\s+[A-Z*(\[]|\s*$)")


def sentences(line: str) -> list[str]:
    """Sentences that are verbatim substrings of the line (usable as fix quotes).
    Trailing citation tags such as '. [S2]' stay attached to the sentence they support."""
    out, start = [], 0
    for m in _SENT_END.finditer(line):
        out.append(line[start:m.end()])
        start = m.end()
    out.append(line[start:])
    return [s for s in (x.strip() for x in out) if s]


_sentences = sentences


def _clean(s: str) -> str:
    s = re.sub(r"\[S\d+(?:\s*,\s*S\d+)*\]|\[activity:[^\]]*\]|\{\{video:S\d+\}\}", " ", s)
    return re.sub(r"[*_`]", "", s)


def _shingle_index(sources: list[dict]) -> dict[tuple, list[str]]:
    idx: dict[tuple, list[str]] = {}
    for src in sources:
        if src["type"] == "video":
            continue
        ws = _words(src.get("text") or "")
        for i in range(len(ws) - SHINGLE + 1):
            idx.setdefault(tuple(ws[i:i + SHINGLE]), []).append(src["id"])
    return idx


def _longest_run(words: list[str], idx: dict) -> tuple[int, set, int]:
    """(longest verbatim run in words, the sources it matches, number of words covered by any run >= SHINGLE)."""
    best, best_src, run, run_src = 0, set(), 0, set()
    covered = [False] * len(words)
    i = 0
    while i + SHINGLE <= len(words):
        hit = idx.get(tuple(words[i:i + SHINGLE]))
        if hit:
            for j in range(i, i + SHINGLE):
                covered[j] = True
            run = run + 1 if run else SHINGLE
            run_src = (run_src | set(hit)) if run > SHINGLE else set(hit)
            if run > best:
                best, best_src = run, set(run_src)
        else:
            run, run_src = 0, set()
        i += 1
    return best, best_src, sum(covered)


def plagiarism(content: str, sources: list[dict]) -> dict:
    """Returns {"ratio", "copied_words", "total_words", "per_source", "passages":[{quote, run, sources}]}."""
    idx = _shingle_index(sources)
    total = copied = 0
    per_source: dict[str, int] = {}
    passages = []
    for line, is_quote in _prose_lines(content):
        for sent in _sentences(line):
            plain = _clean(sent)
            ws = _words(plain)
            total += len(ws)
            if not idx or len(ws) < SHINGLE:
                continue
            run, srcs, cov = _longest_run(ws, idx)
            quoted = is_quote or bool(re.search(r"[\"“”]", plain))
            if cov and not quoted:
                copied += cov
                for sid in srcs:
                    per_source[sid] = per_source.get(sid, 0) + cov
            if run >= MIN_FLAG_RUN and not quoted:
                passages.append({"quote": sent[:300], "run": run, "sources": sorted(srcs)})
    ratio = round(copied / total, 3) if total else 0.0
    passages.sort(key=lambda p: -p["run"])
    return {"ratio": ratio, "copied_words": copied, "total_words": total,
            "per_source": dict(sorted(per_source.items(), key=lambda kv: -kv[1])), "passages": passages[:15]}


def plagiarism_issues(rep: dict) -> list[dict]:
    raw = []
    for p in rep["passages"][:8]:
        srcs = ", ".join(p["sources"]) or "a source"
        raw.append({"severity": "major" if p["run"] >= MAJOR_RUN else "minor", "category": "plagiarism",
                    "quote": p["quote"], "confidence": 0.95,
                    "problem": f"{p['run']} consecutive words match {srcs} verbatim (copying is not acceptable without quotation marks).",
                    "suggestion": "Paraphrase in your own words (keeping the citation), or put the passage in quotation marks and attribute it."})
    pct = round(rep["ratio"] * 100)
    if rep["ratio"] >= TOTAL_CRITICAL:
        raw.append({"severity": "critical", "category": "plagiarism", "quote": "", "confidence": 0.95,
                    "problem": f"About {pct}% of the lesson text is copied verbatim from the sources.",
                    "suggestion": "Rewrite the flagged passages in your own words before publishing."})
    elif rep["ratio"] >= TOTAL_MAJOR:
        raw.append({"severity": "major", "category": "plagiarism", "quote": "", "confidence": 0.9,
                    "problem": f"About {pct}% of the lesson text is copied verbatim from the sources.",
                    "suggestion": "Paraphrase the flagged passages."})
    return raw


# ---------------- prompt injection in fetched pages ----------------
_INJECTION = [
    r"ignore (?:all |any |the |your )?(?:previous|prior|above|earlier) (?:instructions|prompts?|rules)",
    r"disregard (?:all |any |the |your )?(?:previous|prior|above|earlier)? ?(?:instructions|prompts?|rules)",
    r"(?:forget|override) (?:all |your )?(?:previous |prior )?(?:instructions|rules)",
    r"you are (?:now|no longer) (?:an? |the )?(?:\w+ ){0,2}(?:ai|assistant|chatbot|language model|llm|dan|gpt)\b",
    r"(?:reveal|print|show|repeat) (?:your |the )?(?:system|hidden|initial) (?:prompt|instructions)",
    r"\b(?:system|assistant|developer) ?(?:prompt|message)\s*:",
    r"<\|(?:im_start|im_end|system|assistant)\|>",
    r"mark (?:this|these|every|all)[^.]{0,40}\b(?:as )?(?:supported|verified|accurate|correct)\b",
    r"(?:do not|don't|never) (?:cite|mention|flag|report)\b[^.]{0,60}",
    r"as an ai (?:language )?model,? you (?:must|should|will)",
    r"new instructions?\s*:",
]
_INJ_RE = re.compile("|".join(f"(?:{p})" for p in _INJECTION), re.I)


def scan_injection(text: str) -> tuple[str, list[str]]:
    """Removes instruction-like sentences from fetched text. Returns (clean_text, matched_snippets)."""
    if not text:
        return text, []
    hits = []
    kept = []
    for sent in re.split(r"(?<=[.!?])\s+", text):
        m = _INJ_RE.search(sent)
        if m:
            hits.append(m.group(0)[:80])
        else:
            kept.append(sent)
    return " ".join(kept), hits
