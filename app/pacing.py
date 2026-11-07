"""Turns the vague '45 minutes' requirement into a measurable, hard-to-game estimate.

Time = reading prose (130 wpm) + reading code (3x slower) + embedded video (capped at 6 min)
     + knowledge-check thinking time (1 min / question) + hands-on activity time.
Declared activity minutes ([activity: N min]) are NOT trusted blindly: each activity is credited
at most 15 min, at most ~4 words of instructions per minute claimed, and 15 min in total.
"""
import re

from .config import TARGET_MINUTES, WORDS_PER_MINUTE

VIDEO_TOKEN = re.compile(r"\{\{video:(S\d+)\}\}")
ACTIVITY_TOKEN = re.compile(r"\[activity:\s*(\d+)\s*min\]", re.I)
CITE = re.compile(r"\[S\d+(?:\s*,\s*S\d+)*\]")
CODE_FENCE = re.compile(r"(?ms)^```.*?^```[ \t]*$")
TARGET_HINT = re.compile(r"\(about\s+(\d+)(?:\s*-\s*(\d+))?\s*min\)", re.I)
QUESTION = re.compile(r"(?m)^\s*\d+[.)]\s+\S")

VIDEO_WATCH_CAP_MIN = 6
DEFAULT_VIDEO_MIN = 5
CODE_SLOWDOWN = 3
QUIZ_MIN_PER_QUESTION = 1.0
ACTIVITY_MAX_EACH = 15
ACTIVITY_MAX_TOTAL = 15
ACTIVITY_WORDS_PER_MIN = 4
LOW, HIGH = 40, 47


def _words(text: str) -> int:
    text = VIDEO_TOKEN.sub(" ", text)
    text = ACTIVITY_TOKEN.sub(" ", text)
    text = CITE.sub(" ", text)
    return len(re.findall(r"[A-Za-z0-9_'-]+", text))


def split_sections(content: str) -> list[tuple[str, str]]:
    parts = re.split(r"(?m)^##\s+", content)
    out = [("Intro", parts[0])] if parts[0].strip() else []
    for p in parts[1:]:
        head, _, body = p.partition("\n")
        out.append((head.strip(), body))
    return out


def is_quiz(heading: str) -> bool:
    h = heading.lower()
    return "knowledge check" in h or "quiz" in h


def count_questions(body: str) -> int:
    # only the part before the answer key counts as questions
    head = re.split(r"(?i)\*{0,2}answers?\*{0,2}\s*:", body, maxsplit=1)[0]
    return len(QUESTION.findall(head))


def estimate(content: str, sources: list[dict]) -> dict:
    by_id = {s["id"]: s for s in sources}
    sections, notes = [], []
    reading = code = video = quiz = activity = declared = 0.0
    activity_budget = float(ACTIVITY_MAX_TOTAL)
    for head, body in split_sections(content):
        code_words = sum(_words(m.group(0)) for m in CODE_FENCE.finditer(body))
        prose = CODE_FENCE.sub(" ", body)
        words = _words(prose)
        r = words / WORDS_PER_MINUTE
        c = code_words * CODE_SLOWDOWN / WORDS_PER_MINUTE
        v = 0.0
        for sid in VIDEO_TOKEN.findall(body):
            dur = (by_id.get(sid) or {}).get("duration_sec")
            v += min(dur / 60, VIDEO_WATCH_CAP_MIN) if dur else DEFAULT_VIDEO_MIN
        q = count_questions(body) * QUIZ_MIN_PER_QUESTION if is_quiz(head) else 0.0
        a, claims = 0.0, [int(x) for x in ACTIVITY_TOKEN.findall(body)]
        for n in claims:
            declared += n
            credit = min(float(n), float(ACTIVITY_MAX_EACH), max(2.0, words / ACTIVITY_WORDS_PER_MIN))
            if n > ACTIVITY_MAX_EACH:
                notes.append({"kind": "activity_capped", "section": head,
                              "message": f"Activity declares {n} min; credited at most {ACTIVITY_MAX_EACH}."})
            elif credit < n - 0.01:
                notes.append({"kind": "activity_thin", "section": head,
                              "message": f"Activity declares {n} min but its instructions ({words} words) only justify "
                                         f"~{credit:.0f} min; credited {credit:.0f}."})
            if credit > activity_budget:
                notes.append({"kind": "activity_total", "section": head,
                              "message": f"Hands-on time is capped at {ACTIVITY_MAX_TOTAL} min in total; "
                                         f"{credit - activity_budget:.0f} min of this activity is not credited."})
                credit = max(0.0, activity_budget)
            activity_budget -= credit
            a += credit
        if not claims and re.search(r"practice|activity|exercise|lab", head, re.I):
            notes.append({"kind": "activity_undeclared", "section": head,
                          "message": "Practice section has no [activity: N min] declaration, so its hands-on time is not counted."})
        minutes = r + c + v + q + a
        hint = TARGET_HINT.search(head)
        target = (int(hint.group(1)) + int(hint.group(2) or hint.group(1))) / 2 if hint else None
        flag = None
        if target and abs(minutes - target) > max(3.0, 0.5 * target):
            flag = "over" if minutes > target else "under"
        sections.append({"heading": head, "words": words, "minutes": round(minutes, 1),
                         "target": target, "flag": flag})
        reading, code, video, quiz, activity = reading + r, code + c, video + v, quiz + q, activity + a
    total = round(reading + code + video + quiz + activity, 1)
    status = "over" if total > HIGH else "under" if total < LOW else "ok"
    return {"total_minutes": total, "reading": round(reading + code, 1), "code": round(code, 1),
            "video": round(video, 1), "quiz": round(quiz, 1), "activity": round(activity, 1),
            "declared_activity": round(declared, 1), "budget": TARGET_MINUTES, "status": status,
            "words": sum(s["words"] for s in sections), "sections": sections, "notes": notes}
