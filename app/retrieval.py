"""Lightweight passage retrieval (BM25-style, no dependencies).

Used so that long source pages are never blindly truncated: synthesis and QC1 receive the
passages that are *relevant to the objective / to each individual claim*, not just the page head.
"""
import math
import re
from collections import Counter

STOP = set("""a an the and or but if then else of to in on at by for with from as is are was were be been being this that
these those it its into over under about not no can could should would will may might do does did has have had you your we our
their they them he she his her i also than so such more most other some any each which who whom what when where how why""".split())


def tokens(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-z0-9][a-z0-9'_-]*", text.lower()) if w not in STOP and len(w) > 1]


def split_passages(text: str, size: int = 900, overlap: int = 150) -> list[str]:
    text = re.sub(r"\s+", " ", text or "").strip()
    if len(text) <= size:
        return [text] if text else []
    out, i = [], 0
    while i < len(text):
        end = min(len(text), i + size)
        if end < len(text):  # prefer to cut at a sentence boundary near the end of the window
            cut = text.rfind(". ", i + size // 2, end)
            end = cut + 1 if cut != -1 else end
        out.append(text[i:end].strip())
        if end >= len(text):
            break
        i = max(end - overlap, i + 1)
    return out


def rank_passages(query: str, passages: list[str]) -> list[tuple[float, int]]:
    """BM25 scores for each passage; returns [(score, index)] best first (zero-score passages dropped)."""
    q = Counter(tokens(query))
    if not q or not passages:
        return []
    docs = [Counter(tokens(p)) for p in passages]
    n = len(docs)
    avg = sum(sum(d.values()) for d in docs) / max(1, n)
    df = Counter(t for d in docs for t in d)
    scored = []
    for idx, d in enumerate(docs):
        ln = sum(d.values()) or 1
        s = 0.0
        for t in q:
            if t not in d:
                continue
            idf = math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5))
            s += idf * (d[t] * 2.2) / (d[t] + 1.2 * (0.25 + 0.75 * ln / (avg or 1)))
        if s > 0:
            scored.append((s, idx))
    return sorted(scored, reverse=True)


def top_passages(query: str, text: str, k: int = 2, size: int = 900, budget: int | None = None) -> list[str]:
    """The k most relevant passages, returned in their original reading order."""
    passages = split_passages(text, size=size)
    if len(passages) <= k:
        return passages
    best = rank_passages(query, passages)[:k] or [(0.0, 0)]
    chosen = sorted(i for _, i in best)
    out = [passages[i] for i in chosen]
    if budget:
        joined, used = [], 0
        for p in out:
            if used + len(p) > budget:
                p = p[:max(0, budget - used)]
            if p:
                joined.append(p)
                used += len(p)
        return joined
    return out


def excerpt(text: str, query: str, budget: int = 3200, size: int = 800) -> str:
    """Query-relevant excerpt of a long page: opening passage plus the best passages, within budget."""
    passages = split_passages(text, size=size)
    if not passages:
        return ""
    if sum(len(p) for p in passages) <= budget:
        return " ".join(passages)
    picked = {0}
    for _, i in rank_passages(query, passages):
        if sum(len(passages[j]) for j in picked) + len(passages[i]) > budget:
            continue
        picked.add(i)
    return " [...] ".join(passages[i] for i in sorted(picked))


def overlap_ratio(claim: str, evidence: str) -> float:
    """Share of the claim's content words that appear in the evidence (cheap offline support signal)."""
    c = set(tokens(claim))
    return len(c & set(tokens(evidence))) / max(1, len(c))
