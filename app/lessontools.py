"""Deterministic helpers that take the slow, mechanical work away from the lesson agents.

The agents do the judging; these commands do the typing, merging and packaging, so no agent ever re-types a
scraped page, a source list or a report. Nothing here weakens a quality check: the gate (app/gate.py) still
decides PASS or FAIL and re-verifies every evidence quote.

    python -m app.lessontools digest    RUN          candidates_*.json  -> digest.json        (small view for the judges)
    python -m app.lessontools assemble  RUN          relevance + validation + candidates -> sources.json
    python -m app.lessontools excerpts  RUN          sources.json -> source_excerpts.json    (what the writer reads)
    python -m app.lessontools worklist  RUN [--shards N]   lesson + factcheck -> factcheck_todo_<k>.json (claims + evidence passages)
    python -m app.lessontools merge     RUN          factcheck_shard_<k>.json -> factcheck.json
    python -m app.lessontools apply-fixes RUN        applies the safe fixes from both audits, quote for quote
    python -m app.lessontools package   RUN [--no-docx]   gate must PASS -> final/*.md (+ .docx)
    python -m app.lessontools stamp     RUN <label>  records a timestamp in timeline.json
"""
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import docx_export, gate, integrity, pacing, qc, research, retrieval

SEV = {"critical": 0, "major": 1, "minor": 2}
MIN_RELEVANCE = 6
MIN_FIX_CONFIDENCE = 0.6
TOKEN_RE = re.compile(r"\{\{video:S\d+\}\}|\[activity:[^\]]*\]", re.I)
CITE_ID = re.compile(r"\[(S\d+(?:\s*,\s*S\d+)*)\]")


# ---------------- small helpers ----------------
def _read(path: Path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default
    except json.JSONDecodeError as e:
        raise ValueError(f"{Path(path).name} is not valid JSON: {e}")


def _write(path: Path, obj) -> None:
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def cand_id(url: str) -> str:
    return "c" + hashlib.sha1(research._norm_url(url).encode("utf-8")).hexdigest()[:7]


def _file_text(run: Path, c: dict, file_key: str, inline_key: str) -> str:
    if c.get(inline_key):
        return str(c[inline_key])
    f = c.get(file_key)
    if f:
        p = Path(f)
        p = p if p.is_absolute() else run / p
        try:
            return p.read_text(encoding="utf-8")
        except OSError:
            pass
    return ""


def load_candidates(run: Path) -> list[dict]:
    """Every candidate from candidates_*.json (text read from `text_file` when the agent saved it to disk),
    de-duplicated by URL, keeping the version with the most text. Each gets a stable `cand_id`."""
    best: dict[str, dict] = {}
    for f in sorted(run.glob("candidates_*.json")):
        for c in (_read(f, {}) or {}).get("candidates", []):
            if not isinstance(c, dict) or not re.match(r"https?://", str(c.get("url", ""))):
                continue
            c = dict(c)
            c["text"] = _file_text(run, c, "text_file", "text")
            c["transcript"] = _file_text(run, c, "transcript_file", "transcript")
            c["cand_id"] = cand_id(c["url"])
            old = best.get(c["cand_id"])
            if not old or len(c["text"]) + len(c["transcript"]) > len(old["text"]) + len(old["transcript"]):
                best[c["cand_id"]] = c
    return list(best.values())


def _topic_query(plan: dict) -> str:
    return " ".join([plan.get("title", ""), plan.get("objective", "")] + [o.get("text", "") for o in plan.get("outcomes", [])])


# ---------------- digest ----------------
def cmd_digest(run: Path) -> dict:
    plan = _read(run / "plan.json", {})
    query = _topic_query(plan)
    out = []
    for c in load_candidates(run):
        body = c["text"] or c["transcript"]
        out.append({"cand_id": c["cand_id"], "type": c.get("type"), "title": c.get("title"), "url": c["url"],
                    "published": c.get("published"), "chars": len(body), "description_only": bool(c.get("description_only")),
                    "text_file": c.get("text_file") or c.get("transcript_file"),
                    "head": re.sub(r"\s+", " ", body[:300]),
                    "best_passages": retrieval.top_passages(query, body, k=3, size=600) if body else [],
                    **{k: c.get(k) for k in ("video_id", "duration_sec", "channel", "views", "transcript_relevance") if c.get(k) is not None}})
    _write(run / "digest.json", {"note": "Passages are verbatim from each candidate's saved text; full text files are under texts/.",
                                 "candidates": out})
    return {"candidates": len(out), "chars_in_digest": len(json.dumps(out))}


# ---------------- assemble sources.json ----------------
def cmd_assemble(run: Path) -> dict:
    rel = _read(run / "relevance.json", {"scores": []}) or {"scores": []}
    val = _read(run / "validation.json", {"validation": []}) or {"validation": []}
    scores = {s["cand_id"]: s for s in rel.get("scores", []) if isinstance(s, dict) and "cand_id" in s}
    vals = {v["cand_id"]: v for v in val.get("validation", []) if isinstance(v, dict) and "cand_id" in v}
    cands = {c["cand_id"]: c for c in load_candidates(run)}
    kept, rejected, warnings = [], [], []
    for cid, c in cands.items():
        s, v = scores.get(cid), vals.get(cid, {})
        why = None
        if s is None:
            why = "not judged for relevance"
        elif float(s.get("relevance", 0)) < MIN_RELEVANCE:
            why = f"relevance {s.get('relevance')} is below {MIN_RELEVANCE}"
        elif s.get("duplicate_of"):
            why = f"duplicate of {s['duplicate_of']}"
        elif str(v.get("tier", "")).lower() == "reject":
            why = "rejected by the source validator: " + str(v.get("rationale", ""))[:120]
        if why:
            rejected.append({"url": c["url"], "title": c.get("title"), "reason": why})
            continue
        body = c["text"]
        clean, hits = integrity.scan_injection(body) if body else (body, [])
        base = research.reliability(c.get("type", "web"), c["url"], c.get("published"), c.get("views"))
        score = int(max(0, min(100, v.get("score", base["score"]))))
        tier = str(v.get("tier") or ("high" if score >= 75 else "medium" if score >= 55 else "low")).lower()
        if tier not in ("high", "medium", "low"):
            tier = "medium"
        if hits:                                    # a page that tried to instruct the AI loses trust: the tier follows the new score
            score = max(0, score - 25)
            by_score = "high" if score >= 75 else "medium" if score >= 55 else "low"
            tier = max(tier, by_score, key=("high", "medium", "low").index)       # the worse of the two
        if s.get("best_passage") and body and qc._norm(s["best_passage"]) not in qc._norm(body) and c.get("type") != "video":
            warnings.append(f"{c['url']}: the judge's best_passage is not verbatim in the text")
        kept.append({"cand_id": cid, "type": c.get("type", "web"), "title": c.get("title") or c["url"], "url": c["url"],
                     "published": c.get("published"), "snippet": re.sub(r"\s+", " ", (clean or c["transcript"])[:300]), "text": clean,
                     "fetch_ok": bool(clean),
                     "reliability": {"score": score, "tier": tier,
                                     "rationale": str(v.get("rationale") or base["rationale"]) +
                                                  ("; contained instruction-like text (removed)" if hits else "")},
                     "injection_flags": hits[:5], "caveats": v.get("caveats", ""),
                     "video_id": c.get("video_id"), "duration_sec": c.get("duration_sec"), "channel": c.get("channel"),
                     "views": c.get("views"), "transcript": c["transcript"], "author": c.get("author"),
                     "description_only": bool(c.get("description_only")), "relevance": s.get("relevance"),
                     "relevance_reason": s.get("reason", ""), "covers": s.get("covers", []),
                     "_rank": 0.6 * float(s.get("relevance", 0)) * 10 + 0.4 * score})
    order = {"web": 0, "book": 1, "video": 2}
    kept.sort(key=lambda k: (order.get(k["type"], 0), -k["_rank"]))
    idmap = {}
    for n, k in enumerate(kept, 1):
        k["id"] = f"S{n}"
        idmap[k.pop("cand_id")] = k["id"]
        k.pop("_rank")
    by_id = {k["id"]: k for k in kept}
    corroboration = []
    for e in val.get("corroboration", []):
        if not isinstance(e, dict):
            continue
        quotes = {}
        for cid, q in (e.get("quotes") or {}).items():
            sid = idmap.get(cid)
            if sid and qc._norm(str(q)) and qc._norm(str(q)) in qc._norm(by_id[sid]["text"] or by_id[sid]["transcript"]):
                quotes[sid] = q
            elif sid:
                warnings.append(f"corroboration quote for {sid} is not verbatim; dropped: {str(q)[:60]!r}")
        corroboration.append({"fact": e.get("fact", ""), "sources": [idmap[c] for c in e.get("cand_ids", []) if c in idmap],
                              "status": e.get("status", "single_source"), "quotes": quotes})
    text_sources = [k for k in kept if k["type"] != "video"]
    problems = list(rel.get("problems", [])) + list(val.get("problems", [])) + warnings
    for g in rel.get("gaps", []):
        problems.append(f"gap: outcome {g.get('outcome')} needs better sources ({g.get('suggested_query', '')})")
    if len(text_sources) < gate.MIN_SOURCES:
        problems.append(f"only {len(text_sources)} text sources kept; research more")
    _write(run / "sources.json", {"sources": kept, "rejected": rejected, "corroboration": corroboration,
                                  "conflicts": val.get("conflicts", []), "problems": problems})
    return {"kept": len(kept), "by_type": {t: sum(k["type"] == t for k in kept) for t in order}, "rejected": len(rejected),
            "text_sources": len(text_sources), "warnings": len(warnings), "ok": len(text_sources) >= gate.MIN_SOURCES}


# ---------------- excerpts for the architect / writer ----------------
def cmd_excerpts(run: Path, per_source: int = 10, size: int = 800) -> dict:
    plan = _read(run / "plan.json", {})
    sources, _ = gate.load_sources(run)
    raw = _read(run / "sources.json", {}) or {}
    queries = [plan.get("objective", "")] + [o.get("text", "") for o in plan.get("outcomes", [])] + list(plan.get("must_cover", []))
    queries = [q for q in queries if q]
    out = {}
    for s in sources:
        base = {"type": s["type"], "title": s["title"], "url": s["url"], "tier": s["reliability"]["tier"],
                "published": s.get("published"), "caveats": s.get("caveats", "")}
        if s["type"] == "video":
            out[s["id"]] = {**base, "channel": s.get("channel"), "duration_sec": s.get("duration_sec"),
                            "description": s["snippet"], "transcript_head": (s.get("transcript") or "")[:600],
                            "note": "Not citable for facts; only for the Watch and notice slot."}
            continue
        passages = retrieval.split_passages(s["text"], size=size)
        pick: dict[int, float] = {}
        for q in queries:
            ranked = retrieval.rank_passages(q, passages)
            if ranked:
                score, idx = ranked[0]
                pick[idx] = max(pick.get(idx, 0.0), score)
        chosen = sorted(sorted(pick, key=lambda i: -pick[i])[:per_source])
        out[s["id"]] = {**base, "chars": len(s["text"]), "passages": [passages[i] for i in chosen] or passages[:2]}
    _write(run / "source_excerpts.json", {"note": "Passages are verbatim from each source's full text in sources.json. Use only these facts.",
                                          "sources": out, "corroboration": raw.get("corroboration", []), "conflicts": raw.get("conflicts", [])})
    return {"sources": len(out), "chars": len(json.dumps(out))}


# ---------------- fact-check worklist / merge ----------------
def _claim_key(c: dict) -> str:
    return qc._norm(str(c.get("quote") or c.get("claim") or ""))[:60]


def _covered_keys(fc: dict | None) -> set[str]:
    keys = set()
    for c in (fc or {}).get("claims", []):
        keys.add(qc._norm(str(c.get("quote") or ""))[:60])
        keys.add(qc._norm(str(c.get("claim") or ""))[:60])
    return keys


def cmd_worklist(run: Path, shards: int = 1) -> dict:
    sources, _ = gate.load_sources(run)
    lesson = (run / "lesson.md").read_text(encoding="utf-8")
    have = _covered_keys(_read(run / "factcheck.json"))
    todo = []
    for r in qc.extract_claims(lesson):
        if qc._norm(r["quote"])[:60] in have or qc._norm(r["claim"])[:60] in have:
            continue
        todo.append({"quote": r["quote"], "claim": r["claim"], "cited": r["cited"], "kind": r["kind"],
                     "evidence": [{"source": sid, "passage": p} for sid, p in qc._evidence_for(r, sources)]})
    for old in run.glob("factcheck_todo_*.json"):
        old.write_text("{}", encoding="utf-8")                       # stale worklists must not be picked up by mistake
    shards = max(1, min(shards, len(todo) or 1))
    size = -(-len(todo) // shards) if todo else 0
    files = []
    for k in range(shards):
        items = todo[k * size:(k + 1) * size]
        if not items and k:
            continue
        _write(run / f"factcheck_todo_{k + 1}.json", {
            "instructions": "For each item decide a verdict from the EVIDENCE passages (verbatim excerpts of the cited sources); "
                            "evidence_quote must be copied verbatim from a passage (or from the source text via Grep). Copy `quote` exactly.",
            "output_file": f"factcheck_shard_{k + 1}.json", "items": items})
        files.append(f"factcheck_todo_{k + 1}.json")
    return {"claims_to_check": len(todo), "shards": len(files), "files": files}


def cmd_merge(run: Path) -> dict:
    lesson_norm = qc._norm((run / "lesson.md").read_text(encoding="utf-8"))
    existing = _read(run / "factcheck.json", {"claims": [], "issues": []}) or {"claims": [], "issues": []}
    claims = {_claim_key(c): c for c in existing.get("claims", []) if isinstance(c, dict)}
    issues = [i for i in existing.get("issues", []) if isinstance(i, dict)]
    shards = sorted(run.glob("factcheck_shard_*.json"))
    for f in shards:
        d = _read(f, {}) or {}
        for c in d.get("claims", []):
            if isinstance(c, dict):
                claims[_claim_key(c)] = c
        issues += [i for i in d.get("issues", []) if isinstance(i, dict)]
    claims = {k: c for k, c in claims.items() if k and k in lesson_norm}      # drop claims about text that no longer exists
    seen, merged = set(), []
    for i in issues:
        key = (qc._norm(str(i.get("quote", "")))[:60], qc._norm(str(i.get("problem", "")))[:40])
        if key not in seen:
            seen.add(key)
            merged.append(i)
    used = set()
    for n, i in enumerate(merged, 1):
        iid = str(i.get("id", ""))
        i["id"] = iid if iid.startswith("F") and iid not in used else f"F{n}"
        used.add(i["id"])
    claim_list = list(claims.values())
    counts = {v: sum(c.get("verdict") == v for c in claim_list) for v in gate.VERDICTS}
    summary = f"{len(claim_list)} claims checked: " + ", ".join(f"{n} {v}" for v, n in counts.items() if n) + f"; {len(merged)} issue(s)."
    _write(run / "factcheck.json", {"model": existing.get("model") or "see shards", "claims": claim_list, "issues": merged, "summary": summary})
    return {"claims": len(claim_list), "issues": len(merged), "shards_merged": len(shards), "verdicts": counts}


# ---------------- apply the safe fixes ----------------
def _uncited_count(text: str) -> int:
    n = 0
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith(("#", "|", ">", "```")):
            continue
        for sent in integrity.sentences(line):
            plain = re.sub(r"[*_`]", "", sent)
            if len(plain.split()) >= 12 and not qc.CITE_RE.search(sent) and not plain.lstrip().lower().startswith("example") \
                    and not plain.rstrip().endswith("?"):
                n += 1
    return n


def _blockers(content: str, sources: list[dict]) -> set[str]:
    return {c["id"] for c in gate.check_lesson(content, sources) if c["status"] == "fail" and c["blocker"]}


def cmd_apply_fixes(run: Path) -> dict:
    sources, _ = gate.load_sources(run)
    lesson = (run / "lesson.md").read_text(encoding="utf-8")
    files = {"factcheck": _read(run / "factcheck.json", {"issues": []}) or {"issues": []},
             "pedagogy": _read(run / "pedagogy.json", {"issues": []}) or {"issues": []}}
    valid = {s["id"] for s in sources if s["type"] != "video"}
    queue = [(name, i) for name, d in files.items() for i in d.get("issues", []) if isinstance(i, dict) and i.get("status", "open") == "open"]
    queue.sort(key=lambda x: (SEV.get(x[1].get("severity"), 3), -float(x[1].get("confidence", 0.7) or 0.7)))
    base_blockers, base_ok = _blockers(lesson, sources), pacing.estimate(lesson, sources)["status"] == "ok"
    applied, human = [], []

    def skip(name, i, reason):
        i["status"], i["reason"] = "needs_human", reason
        human.append({"file": name, "id": i.get("id"), "severity": i.get("severity"), "reason": reason, "problem": str(i.get("problem", ""))[:160]})

    for name, i in queue:
        q, r = str(i.get("quote") or ""), str(i.get("replacement") or "")
        if not q or not r:
            skip(name, i, "no exact replacement was offered")
        elif lesson.count(q) != 1:
            skip(name, i, "the flagged text is not in the lesson exactly once")
        elif float(i.get("confidence", 0.7) or 0.7) < MIN_FIX_CONFIDENCE:
            skip(name, i, "the auditor's confidence is too low to apply automatically")
        elif any(t not in r for t in TOKEN_RE.findall(q)):
            skip(name, i, "the replacement would remove a video or activity marker")
        elif any(sid not in valid for m in CITE_ID.finditer(r) for sid in re.findall(r"S\d+", m.group(1))):
            skip(name, i, "the replacement cites a source that does not exist or is a video")
        elif _uncited_count(r) > _uncited_count(q):
            skip(name, i, "the replacement adds a statement without a citation")
        else:
            trial = lesson.replace(q, r, 1)
            if base_ok and pacing.estimate(trial, sources)["status"] != "ok":
                skip(name, i, "applying it would break the 40-47 minute budget")
            elif _blockers(trial, sources) - base_blockers:
                skip(name, i, "applying it would introduce a new gate failure")
            else:
                lesson = trial
                i["status"] = "applied"
                applied.append({"file": name, "id": i.get("id"), "severity": i.get("severity"), "replacement": r})
    (run / "lesson.md").write_text(lesson, encoding="utf-8")
    for name, d in files.items():
        if d.get("issues"):
            _write(run / f"{name}.json", d)
    report = {"applied": applied, "needs_human": human, "changed_texts": [a["replacement"] for a in applied]}
    _write(run / "fixes_report.json", report)
    return {"applied": len(applied), "needs_human": len(human), "changed_texts": len(applied)}


# ---------------- package the deliverables ----------------
def _cell(t) -> str:
    return re.sub(r"\s+", " ", str(t or "")).replace("|", "\\|").strip()


def _issues_md(issues: list[dict]) -> list[str]:
    if not issues:
        return ["_No issues reported._", ""]
    out = []
    for i in sorted(issues, key=lambda x: SEV.get(x.get("severity"), 3)):
        out.append(f"### {i.get('id', '?')} - {str(i.get('severity', '')).upper()} - {i.get('category', '')}  [{i.get('status', 'open')}]")
        if i.get("quote"):
            out.append(f"- **Flagged text:** > {i['quote']}")
        out.append(f"- **Problem:** {i.get('problem', '')}")
        if i.get("suggestion"):
            out.append(f"- **Suggestion:** {i['suggestion']}")
        if i.get("replacement"):
            out.append(f"- **Proposed replacement:** {i['replacement']}")
        if i.get("reason"):
            out.append(f"- **Why it was not applied automatically:** {i['reason']}")
        out.append("")
    return out


def _timeline(run: Path) -> list[tuple[str, float]]:
    marks = _read(run / "timeline.json", []) or []
    return [(m["label"], float(m["epoch"])) for m in marks if isinstance(m, dict) and "epoch" in m]


def cmd_package(run: Path, docx: bool = True) -> dict:
    report = gate.run_gate(run, "audit")
    if report["verdict"] != "PASS":
        return {"ok": False, "error": "the audit gate does not pass; refusing to package a failing lesson", "blockers": report["blockers"]}
    sources, _ = gate.load_sources(run)
    lesson = (run / "lesson.md").read_text(encoding="utf-8")
    fc, pg, plan = _read(run / "factcheck.json", {}), _read(run / "pedagogy.json", {}), _read(run / "plan.json", {})
    est = pacing.estimate(lesson, sources)
    final = run / "final"
    final.mkdir(exist_ok=True)
    (final / "lesson.md").write_text(lesson, encoding="utf-8")
    # references
    cited = {sid for m in CITE_ID.finditer(lesson) for sid in re.findall(r"S\d+", m.group(1))}
    ref = ["# References", ""]
    for kind, label in (("web", "Web"), ("book", "Books"), ("video", "Videos")):
        items = [s for s in sources if s["type"] == kind]
        if items:
            ref += [f"## {label}", ""]
            for s in items:
                used = "cited in the lesson" if s["id"] in cited else ("embedded in the lesson" if f"{{{{video:{s['id']}}}}}" in lesson else "not cited")
                extra = f" - {s['author']}" if s.get("author") else (f" - {s['channel']}" if s.get("channel") else "")
                ref.append(f"- **[{s['id']}]** [{s['title']}]({s['url']}){extra} (reliability: {s['reliability']['tier']}; {used})")
                if s.get("caveats"):
                    ref.append(f"  - Note: {s['caveats']}")
            ref.append("")
    (final / "references.md").write_text("\n".join(ref), encoding="utf-8")
    # QC 1
    claims = fc.get("claims", [])
    counts = {v: sum(c.get("verdict") == v for c in claims) for v in gate.VERDICTS}
    q1 = ["# QC Layer 1: Research and Factual Accuracy", "", f"**Lesson:** {plan.get('title', '')}  ", f"**Objective:** {plan.get('objective', '')}  ",
          f"**Auditor model:** {fc.get('model', '')}  ", f"**Gate:** {report['verdict']} (evidence quotes re-verified by code against the source text)  ", "",
          "## Summary", "", fc.get("summary", ""), "", "## Claim verification", "",
          f"{len(claims)} claims: " + ", ".join(f"{n} {v}" for v, n in counts.items() if n) + ".", "",
          "| Verdict | Claim | Cited | Evidence from source |", "|---|---|---|---|"]
    q1 += [f"| {c.get('verdict', '')} | {_cell(c.get('claim'))} | {', '.join(c.get('cited') or [])} | {_cell(c.get('evidence_quote'))} |" for c in claims]
    q1 += ["", "## Issues and suggested improvements", ""] + _issues_md(fc.get("issues", []))
    (final / "qc_report_1_factual.md").write_text("\n".join(q1), encoding="utf-8")
    # QC 2
    q2 = ["# QC Layer 2: Instructional Quality", "", f"**Lesson:** {plan.get('title', '')}  ", f"**Auditor model:** {pg.get('model', '')}  ", "",
          "## Summary", "", pg.get("summary", ""), "", "## Pacing against the 45-minute budget", "",
          f"Measured **{est['total_minutes']} min** (reading {est['reading']}, video {est['video']}, quiz {est['quiz']}, activity {est['activity']}): {est['status']}.", "",
          "| Section | Words | Minutes |", "|---|---|---|"]
    q2 += [f"| {_cell(s['heading'])} | {s['words']} | {s['minutes']} |" for s in est["sections"]]
    q2 += ["", "## Learning-objective coverage", "", "| Outcome | Taught | Practised | Assessed | Where |", "|---|---|---|---|---|"]
    yn = lambda v: "yes" if v else "NO"
    q2 += [f"| {_cell(str(o.get('id', '')) + ' ' + str(o.get('outcome', '')))} | {yn(o.get('taught'))} | {yn(o.get('practiced'))} | {yn(o.get('assessed'))} | {_cell(o.get('where'))} |"
           for o in pg.get("objective_outcomes", [])]
    q2 += ["", "## Quality dimensions (1-5)", "", "| Dimension | Score | Comment |", "|---|---|---|"]
    q2 += [f"| {k.replace('_', ' ')} | {v.get('score', '')} | {_cell(v.get('comment'))} |" for k, v in (pg.get("dimensions") or {}).items()]
    q2 += ["", "## Issues and suggested improvements", ""] + _issues_md(pg.get("issues", []))
    (final / "qc_report_2_instructional.md").write_text("\n".join(q2), encoding="utf-8")
    # summary
    allissues = [("QC 1", i) for i in fc.get("issues", [])] + [("QC 2", i) for i in pg.get("issues", [])]
    stat = lambda s: sum(i.get("status", "open") == s for _, i in allissues)
    marks = _timeline(run)
    tl = []
    if len(marks) >= 2:
        tl = ["", "## Timing", "", "| Phase | Minutes |", "|---|---|"] + [
            f"| {marks[k][0]} -> {marks[k + 1][0]} | {(marks[k + 1][1] - marks[k][1]) / 60:.1f} |" for k in range(len(marks) - 1)] + [
            f"| **Total** | **{(marks[-1][1] - marks[0][1]) / 60:.1f}** |"]
    summ = [f"# Run summary: {plan.get('title', '')}", "", f"**Objective:** {plan.get('objective', '')}", "",
            "## Result", "", f"- **Gate:** {report['verdict']} (audit): {report['passed']} checks passed, {report['blockers']} blocking, {report['warnings']} warning(s).",
            f"- **Measured duration:** {est['total_minutes']} minutes (allowed 40-47).",
            f"- **Claims verified:** {len(claims)} (" + ", ".join(f"{n} {v}" for v, n in counts.items() if n) + ").",
            f"- **Sources:** {len(sources)} (" + ", ".join(f"{sum(s['type'] == t for s in sources)} {t}" for t in ('web', 'book', 'video')) + ").",
            f"- **Issues:** {len(allissues)} found, {stat('applied')} applied automatically, {stat('open')} open, {stat('needs_human')} need a human.", ""]
    if report["next_actions"]:
        summ += ["## Gate warnings", ""] + [f"- {a}" for a in report["next_actions"]] + [""]
    still = [(src, i) for src, i in allissues if i.get("status", "open") != "applied"]
    if still:
        summ += ["## Still open", ""] + [f"- {src} {i.get('id')} ({i.get('severity')}, {i.get('status', 'open')}): {str(i.get('problem', ''))[:140]}"
                                           for src, i in still] + [""]
    summ += tl + ["", "## Honest limits", "",
                  "- Facts were verified by an AI fact-checker against the source text; the evidence quotes were re-checked by code. An instructor should still read the lesson.",
                  "- Books and videos are only as verifiable as the text that could be fetched; videos are never cited for facts.", ""]
    (final / "summary.md").write_text("\n".join(summ), encoding="utf-8")
    out = {"ok": True, "final": sorted(p.name for p in final.glob("*.md"))}
    if docx:
        out["docx"] = [d.name for _, d in docx_export.convert(final, run / "sources.json")]
    return out


# ---------------- timeline ----------------
def cmd_stamp(run: Path, label: str) -> dict:
    marks = _read(run / "timeline.json", []) or []
    now = datetime.now(timezone.utc)
    marks.append({"label": label, "at": now.isoformat(timespec="seconds"), "epoch": now.timestamp()})
    _write(run / "timeline.json", marks)
    return {"label": label, "minutes_since_start": round((now.timestamp() - marks[0]["epoch"]) / 60, 1)}


# ---------------- CLI ----------------
def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[0] not in ("digest", "assemble", "excerpts", "worklist", "merge", "apply-fixes", "package", "stamp"):
        print(__doc__)
        return 2
    cmd, run = argv[0], Path(argv[1])
    try:
        if cmd == "digest":
            out = cmd_digest(run)
        elif cmd == "assemble":
            out = cmd_assemble(run)
        elif cmd == "excerpts":
            out = cmd_excerpts(run)
        elif cmd == "worklist":
            out = cmd_worklist(run, int(argv[argv.index("--shards") + 1]) if "--shards" in argv else 1)
        elif cmd == "merge":
            out = cmd_merge(run)
        elif cmd == "apply-fixes":
            out = cmd_apply_fixes(run)
        elif cmd == "package":
            out = cmd_package(run, "--no-docx" not in argv)
        else:
            out = cmd_stamp(run, argv[2] if len(argv) > 2 else "mark")
    except (OSError, ValueError, KeyError, gate.GateInputError) as e:
        print(json.dumps({"ok": False, "error": f"{type(e).__name__}: {e}"}))
        return 1
    print(json.dumps(out, ensure_ascii=False))
    return 0 if out.get("ok", True) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
