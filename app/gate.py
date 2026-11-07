"""Deterministic acceptance gate for lessons produced by a team of agents (files in, verdict out).

LLM agents write and judge; this gate cannot be talked round. It re-checks, with code, everything that can be
checked with code, and verifies the auditors' work (their evidence quotes must really occur in the source text).

    python -m app.gate check <run_dir> [--phase draft|audit]

Run directory contract (see skills/hire-athul-lesson-maker/references/contracts.md):
    sources.json    {"sources": [{id, type, title, url, reliability, text, ...}]}      required
    lesson.md       the lesson with inline [Sx] citations                               required
    plan.json       {"outcomes": [{id, text}], ...}                                     optional
    factcheck.json  {"claims": [{claim, quote, cited, verdict, evidence_quote, ...}], "issues": [...]}   audit phase
    pedagogy.json   {"objective_outcomes": [...], "dimensions": {...}, "issues": [...]}                   audit phase
Writes gate_report.json next to them and exits 0 on PASS, 1 on FAIL, 2 on unreadable input.
"""
import json
import re
import sys
from pathlib import Path

from . import integrity, pacing, qc

VERDICTS = ("supported", "partially_supported", "unsupported", "contradicted", "unverifiable")
MIN_SOURCES = 3
MAX_UNVERIFIED_SHARE = 0.20
MIN_CLAIM_COVERAGE = 0.90
MIN_EVIDENCE_CHARS = 12


class GateInputError(ValueError):
    pass


def _read_json(path: Path, required: bool = False):
    if not path.exists():
        if required:
            raise GateInputError(f"{path.name} is missing.")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise GateInputError(f"{path.name} is not valid JSON: {e}")


def load_sources(run_dir: Path) -> tuple[list[dict], list[str]]:
    raw = _read_json(run_dir / "sources.json", required=True)
    items = raw.get("sources") if isinstance(raw, dict) else raw
    if not isinstance(items, list):
        raise GateInputError("sources.json must be a list or {\"sources\": [...]}.")
    out, errors = [], []
    for i, s in enumerate(items):
        if not isinstance(s, dict):
            errors.append(f"source #{i + 1} is not an object")
            continue
        sid = str(s.get("id", ""))
        if not re.fullmatch(r"S\d+", sid):
            errors.append(f"source #{i + 1}: id '{sid}' must look like S1")
        if s.get("type") not in ("web", "book", "video"):
            errors.append(f"{sid or i + 1}: type must be web, book or video")
        if not re.match(r"https?://", str(s.get("url", ""))):
            errors.append(f"{sid or i + 1}: url must be http(s)")
        text = str(s.get("text") or "")
        out.append({**s, "id": sid, "title": str(s.get("title") or s.get("url") or sid),
                    "snippet": str(s.get("snippet") or text[:300]), "text": text,
                    "fetch_ok": bool(s.get("fetch_ok", bool(text))),
                    "reliability": {"tier": "medium", "score": 55, "rationale": "", **(s.get("reliability") or {})}})
    if len({s["id"] for s in out}) != len(out):
        errors.append("source ids are not unique")
    return out, errors


def _check(cid: str, name: str, status: str, detail: str = "", blocker: bool = True, fix: str = "") -> dict:
    return {"id": cid, "name": name, "status": status, "blocker": blocker, "detail": detail, "fix": fix}


def _ok(cid, name, detail=""):
    return _check(cid, name, "pass", detail)


# ---------------- draft checks (no auditors needed) ----------------
def check_sources(sources: list[dict], schema_errors: list[str]) -> list[dict]:
    out = []
    out.append(_check("schema", "sources.json is well-formed", "fail", "; ".join(schema_errors[:5]),
                      fix="Fix sources.json so every source has a unique id (S1..), type, title and http(s) url.")
               if schema_errors else _ok("schema", "sources.json is well-formed"))
    non_video = [s for s in sources if s["type"] != "video"]
    out.append(_ok("source_count", "At least 3 text sources", f"{len(non_video)} text sources") if len(non_video) >= MIN_SOURCES else
               _check("source_count", "At least 3 text sources", "fail", f"only {len(non_video)} text source(s)",
                      fix="Research more: the lesson needs at least 3 independent text sources."))
    kinds = {s["type"] for s in sources}
    missing = [k for k in ("web", "book", "video") if k not in kinds]
    out.append(_ok("source_mix", "Web, book and video sources present") if not missing else
               _check("source_mix", "Web, book and video sources present", "fail", "missing: " + ", ".join(missing),
                      blocker=False, fix="Add at least one source of each missing type, or state in the report why none exists."))
    thin = [s["id"] for s in non_video if len(s["text"]) < 300]
    out.append(_ok("source_text", "Every text source has real text") if not thin else
               _check("source_text", "Every text source has real text", "fail",
                      f"{', '.join(thin)} have under 300 characters of text; claims citing them cannot be verified",
                      blocker=False, fix="Scrape the full page (python -m app.scraper fetch <url>) or drop the source."))
    return out


def check_lesson(content: str, sources: list[dict]) -> list[dict]:
    out = []
    ids = {s["id"]: s for s in sources}
    # citations and source hygiene (reuses the app's deterministic QC 1 checks)
    det = qc._qc1_deterministic(content, sources)
    bad = [i for i in det if i["severity"] == "critical" and i["category"] != "factual_error"
           or (i["severity"] == "major" and "video" in i["problem"])]
    out.append(_ok("citations", "Every citation is valid and none cites a video") if not bad else
               _check("citations", "Every citation is valid and none cites a video", "fail",
                      "; ".join(f"{i['quote'] or '-'}: {i['problem']}" for i in bad[:4]),
                      fix="Replace or remove the listed citations; videos may never support a factual claim."))
    uncited = [i for i in det if "carries no source citation" in i["problem"]]
    out.append(_ok("uncited", "No uncited substantive statements") if not uncited else
               _check("uncited", "No uncited substantive statements", "fail", f"{len(uncited)} statement(s), e.g. {uncited[0]['quote'][:90]!r}",
                      blocker=len(uncited) > 3, fix="Cite each statement to a source that says it, or delete/soften it."))
    status_err = [i for i in det if i["category"] == "factual_error"]
    out.append(_ok("status_classes", "No status-code class contradictions") if not status_err else
               _check("status_classes", "No status-code class contradictions", "fail", status_err[0]["problem"],
                      fix="Correct the status class in: " + status_err[0]["quote"][:120]))
    flagged = [s["id"] for s in sources if s.get("injection_flags")]
    out.append(_ok("injection", "No source carried prompt-injection text") if not flagged else
               _check("injection", "No source carried prompt-injection text", "fail",
                      f"{', '.join(flagged)} contained instruction-like text (removed); prefer other sources",
                      blocker=False, fix="Do not rely on the flagged sources for key claims."))
    # originality
    plag = integrity.plagiarism(content, sources)
    big = [p for p in plag["passages"] if p["run"] >= integrity.MAJOR_RUN]
    if plag["ratio"] >= integrity.TOTAL_MAJOR or big:
        out.append(_check("originality", "Lesson text is original", "fail",
                          f"{round(plag['ratio'] * 100)}% verbatim, {len(plag['passages'])} copied passage(s)",
                          fix="Paraphrase: " + " | ".join(p["quote"][:80] for p in plag["passages"][:3])))
    elif plag["passages"]:
        out.append(_check("originality", "Lesson text is original", "fail", f"{len(plag['passages'])} borderline copied passage(s)",
                          blocker=False, fix="Paraphrase: " + plag["passages"][0]["quote"][:100]))
    else:
        out.append(_ok("originality", "Lesson text is original", f"{round(plag['ratio'] * 100)}% verbatim"))
    # pacing
    est = pacing.estimate(content, sources)
    out.append(_ok("pacing", "Measured duration is 40-47 minutes", f"{est['total_minutes']} min") if est["status"] == "ok" else
               _check("pacing", "Measured duration is 40-47 minutes", "fail",
                      f"{est['total_minutes']} min ({est['status']}): reading {est['reading']}, video {est['video']}, "
                      f"quiz {est['quiz']}, activity {est['activity']} of {est['declared_activity']} declared",
                      fix=("Cut the longest sections." if est["status"] == "over" else "Add sourced material, an example or a longer activity.")))
    if est["notes"]:
        out.append(_check("activity", "Declared activity time is credible", "fail", "; ".join(n["message"] for n in est["notes"][:3]),
                          blocker=False, fix="Write fuller step-by-step instructions or lower the declared minutes."))
    # structure and assessment
    heads = " ".join(h.lower() for h, _ in qc._sections(content))
    need = [("knowledge check" in heads or "quiz" in heads, "a Knowledge check section"),
            ("practice" in heads or "activity" in heads, "a hands-on Practice/Activity section"),
            ("example" in content.lower(), "a concrete example"),
            ("wrap" in heads or "summary" in heads or "recap" in heads, "a Wrap-up section"),
            ("{{video:" in content, "an embedded video")]
    gaps = [label for ok, label in need if not ok]
    out.append(_ok("structure", "Lesson has all required parts") if not gaps else
               _check("structure", "Lesson has all required parts", "fail", "missing " + ", ".join(gaps),
                      blocker=any(g.startswith(("a Knowledge", "a hands-on")) for g in gaps), fix="Add " + ", ".join(gaps) + "."))
    vids = [m for m in re.findall(r"\{\{video:(S\d+)\}\}", content) if m not in ids or ids[m]["type"] != "video"]
    if vids:
        out.append(_check("video_tokens", "Video tokens point at video sources", "fail", ", ".join(vids), fix="Fix the {{video:Sx}} ids."))
    quiz = qc.parse_quiz(content)
    unanswered = [q["n"] for q in quiz if not q["answer"]]
    if len(quiz) < 3 or unanswered:
        out.append(_check("quiz", "Knowledge check has questions and a full answer key", "fail",
                          f"{len(quiz)} question(s); unanswered: {unanswered or 'none'}", fix="Write 5 questions, each with an answer in the key."))
    else:
        out.append(_ok("quiz", "Knowledge check has questions and a full answer key", f"{len(quiz)} questions"))
    unused = [s["id"] for s in sources if s["type"] != "video" and not re.search(rf"\b{s['id']}\b", content)]
    out.append(_ok("references", "Every text source is cited") if not unused else
               _check("references", "Every text source is cited", "fail", f"never cited: {', '.join(unused)}", blocker=False,
                      fix="Cite them where relevant or remove them from the reference list."))
    return out


# ---------------- audit checks (verify the auditors) ----------------
def check_factcheck(fc: dict, content: str, sources: list[dict]) -> list[dict]:
    out, ids = [], {s["id"]: s for s in sources}
    claims = [c for c in (fc.get("claims") or []) if isinstance(c, dict)]
    texts = {sid: qc._norm(s["text"] or s["snippet"]) for sid, s in ids.items()}
    fabricated, verified = [], []
    for c in claims:
        ev = str(c.get("evidence_quote") or "")
        cited = [x for x in (c.get("cited") or []) if x in ids] or list(ids)
        if ev:
            ne = qc._norm(ev)
            if len(ne) < MIN_EVIDENCE_CHARS or not any(ne in texts[x] for x in cited):
                fabricated.append(c)
                c = {**c, "verdict": "unverifiable"}
        elif c.get("verdict") in ("supported", "partially_supported"):
            fabricated.append(c)                     # a 'supported' verdict with no evidence at all
            c = {**c, "verdict": "unverifiable"}
        verified.append(c)
    out.append(_ok("evidence", "Every evidence quote really occurs in its source", f"{len(claims)} claims checked") if not fabricated else
               _check("evidence", "Every evidence quote really occurs in its source", "fail",
                      f"{len(fabricated)} claim(s) have invented or missing evidence, e.g. {str(fabricated[0].get('claim', ''))[:80]!r}",
                      fix="Send these claims back to the fact-checker: it must quote the source verbatim or mark them unverifiable."))
    required = qc.extract_claims(content)
    have = {qc._norm(str(c.get("quote") or ""))[:60] for c in claims} | {qc._norm(str(c.get("claim") or ""))[:60] for c in claims}
    covered = sum(1 for r in required if qc._norm(r["quote"])[:60] in have or qc._norm(r["claim"])[:60] in have)
    cov = covered / len(required) if required else 1.0
    out.append(_ok("coverage", "Fact-check covered the cited claims and quiz answers", f"{covered}/{len(required)}") if cov >= MIN_CLAIM_COVERAGE else
               _check("coverage", "Fact-check covered the cited claims and quiz answers", "fail", f"only {covered}/{len(required)} ({cov:.0%})",
                      fix="Ask the fact-checker to cover every cited sentence and every quiz answer."))
    counts = {v: sum(1 for c in verified if c.get("verdict") == v) for v in VERDICTS}
    contradicted = [c for c in verified if c.get("verdict") == "contradicted"]
    out.append(_ok("contradictions", "No claim is contradicted by its sources") if not contradicted else
               _check("contradictions", "No claim is contradicted by its sources", "fail",
                      "; ".join(str(c.get("claim"))[:90] for c in contradicted[:3]),
                      fix="Correct each contradicted claim to match the sources, then re-run the fact-check on it."))
    weak = counts["unsupported"] + counts["unverifiable"]
    share = weak / len(verified) if verified else 0.0
    out.append(_ok("support", "At least 80% of claims are supported", f"{counts['supported']} supported, {counts['partially_supported']} partial, {weak} weak")
               if share <= MAX_UNVERIFIED_SHARE else
               _check("support", "At least 80% of claims are supported", "fail", f"{weak}/{len(verified)} unsupported or unverifiable ({share:.0%})",
                      fix="Rewrite or remove unsupported claims, or research better sources for them."))
    openc = [i for i in (fc.get("issues") or []) if isinstance(i, dict) and i.get("severity") == "critical" and i.get("status", "open") == "open"]
    out.append(_ok("fact_issues", "No open critical factual issue") if not openc else
               _check("fact_issues", "No open critical factual issue", "fail", "; ".join(str(i.get("problem"))[:90] for i in openc[:3]),
                      fix="Apply or resolve every critical issue."))
    return out


def check_pedagogy(pg: dict, plan: dict | None) -> list[dict]:
    out = []
    outcomes = [o for o in (pg.get("objective_outcomes") or []) if isinstance(o, dict)]
    gaps = [o.get("outcome", "?") for o in outcomes if not (o.get("taught") and o.get("practiced") and o.get("assessed"))]
    out.append(_ok("coverage_matrix", "Every outcome is taught, practised and assessed", f"{len(outcomes)} outcomes") if outcomes and not gaps else
               _check("coverage_matrix", "Every outcome is taught, practised and assessed", "fail",
                      "no outcomes reported" if not outcomes else "gaps: " + "; ".join(str(g)[:70] for g in gaps[:4]),
                      fix="Add teaching, practice or a quiz question for each gap."))
    if plan and isinstance(plan.get("outcomes"), list) and outcomes and len(outcomes) < len(plan["outcomes"]):
        out.append(_check("plan_outcomes", "Reviewer covered all planned outcomes", "fail",
                          f"plan has {len(plan['outcomes'])} outcomes, review lists {len(outcomes)}", blocker=False,
                          fix="Ask the reviewer to assess every planned outcome."))
    openc = [i for i in (pg.get("issues") or []) if isinstance(i, dict) and i.get("severity") == "critical" and i.get("status", "open") == "open"]
    out.append(_ok("pedagogy_issues", "No open critical instructional issue") if not openc else
               _check("pedagogy_issues", "No open critical instructional issue", "fail", "; ".join(str(i.get("problem"))[:90] for i in openc[:3]),
                      fix="Apply or resolve every critical issue."))
    low = [k for k, v in (pg.get("dimensions") or {}).items() if isinstance(v, dict) and isinstance(v.get("score"), (int, float)) and v["score"] < 3]
    out.append(_ok("dimensions", "All quality dimensions score 3 or more") if not low else
               _check("dimensions", "All quality dimensions score 3 or more", "fail", ", ".join(low), blocker=False,
                      fix="Improve: " + ", ".join(low)))
    return out


# ---------------- entry points ----------------
def run_gate(run_dir: Path, phase: str = "audit") -> dict:
    run_dir = Path(run_dir)
    sources, schema_errors = load_sources(run_dir)
    lp = run_dir / "lesson.md"
    if not lp.exists():
        raise GateInputError("lesson.md is missing.")
    content = lp.read_text(encoding="utf-8")
    if not content.strip():
        raise GateInputError("lesson.md is empty.")
    checks = check_sources(sources, schema_errors) + check_lesson(content, sources)
    if phase == "audit":
        fc, pg, plan = _read_json(run_dir / "factcheck.json"), _read_json(run_dir / "pedagogy.json"), _read_json(run_dir / "plan.json")
        checks += check_factcheck(fc, content, sources) if fc else [_check(
            "factcheck_present", "factcheck.json exists", "fail", "the independent fact-check has not run", fix="Run kl-fact-checker.")]
        checks += check_pedagogy(pg, plan) if pg else [_check(
            "pedagogy_present", "pedagogy.json exists", "fail", "the instructional review has not run", fix="Run kl-pedagogy-reviewer.")]
    blockers = [c for c in checks if c["status"] == "fail" and c["blocker"]]
    warnings = [c for c in checks if c["status"] == "fail" and not c["blocker"]]
    report = {"phase": phase, "verdict": "FAIL" if blockers else "PASS", "blockers": len(blockers), "warnings": len(warnings),
              "passed": sum(c["status"] == "pass" for c in checks), "checks": checks,
              "next_actions": [f"[{c['id']}] {c['fix']}" for c in blockers + warnings if c["fix"]]}
    (run_dir / "gate_report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    return report


def render(report: dict) -> str:
    lines = [f"GATE {report['verdict']} ({report['phase']}): {report['passed']} passed, {report['blockers']} blocking, {report['warnings']} warning(s)"]
    for c in report["checks"]:
        mark = "PASS" if c["status"] == "pass" else ("FAIL" if c["blocker"] else "WARN")
        lines.append(f"  [{mark}] {c['name']}" + (f" - {c['detail']}" if c["detail"] else ""))
    if report["next_actions"]:
        lines += ["", "NEXT ACTIONS"] + [f"  - {a}" for a in report["next_actions"]]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[0] != "check":
        print(__doc__)
        return 2
    phase = argv[argv.index("--phase") + 1] if "--phase" in argv else "audit"
    try:
        report = run_gate(Path(argv[1]), phase)
    except GateInputError as e:
        print(f"GATE ERROR: {e}")
        return 2
    print(render(report))
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
