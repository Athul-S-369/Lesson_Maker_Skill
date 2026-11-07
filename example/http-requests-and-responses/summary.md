# Run summary: HTTP Requests and Responses

**Objective:** Explain GET and POST methods and distinguish between 2xx, 4xx, and 5xx response status categories. Learner: intermediate, self-study.
**Produced by:** the `kelvium-lesson-builder` skill (12 specialised agents plus a deterministic code gate). Mock/offline mode was not used: all sources were scraped live.

## Result
- **Gate:** `GATE PASS (audit)`: 20 checks passed, 0 blocking, 1 warning (source S15 is never cited, see below). I re-ran the gate myself after the last edit; it passed.
- **Measured duration:** 46.0 minutes (allowed 40-47). The minutes written in the section headings add up to 48.5 because the quiz heading now says "about 9 min" (the quiz measures about 9 min) while the activity token says 6; the gate measures the real reading, video, quiz and activity time, not the labels.
- **Claims verified:** 146 (140 supported, 3 partially supported, 3 unverifiable, 0 unsupported, 0 contradicted). The gate re-checked every evidence quote: each occurs verbatim in its cited source. Coverage: 45 of 45 cited sentences and quiz answers.
- **Outcomes:** all 6 are taught, practised and assessed.
- **Originality:** 1% of the lesson text is a verbatim run of 8+ words from a source.

## Sources (18)
- **Web, 13:** RFC 9110 (methods section), MDN (Messages, GET, POST, Forms, Status, 401), W3C TAG finding on GET and POST, Cloudflare, Wikipedia (HTTP; list of status codes), http.dev, restfulapi.net. All cited in the lesson.
- **Books, 2:** *Computer Networks: A Systems Approach* (S14, cited) and the open textbook chapter by Bonaventure (S15, listed but not cited: its sentence on 3xx codes is wrong). The fetched pages showed no author, publisher or year, so those details are unverified and left blank.
- **Videos, 3:** S17 is embedded in "Watch and notice". S16 and S18 are not used (S16 spends a quarter on out-of-scope 3xx codes; S18's analogy reinforces the "POST is secure" misconception). Videos are never cited for facts.

## Issues
| Audit | Found | Applied | Still open |
|---|---|---|---|
| Fact-check (QC 1), first pass | 7 minor | 5 (F1, F2, F4, F5, F6) | 2 need a human: F3 (no cited source names the host as a URL part), F7 (the notes about video S17's content cannot be checked against a transcript) |
| Instructional (QC 2), first pass | 16 (3 major, all in the quiz) | 8 | superseded by the second pass |
| Instructional (QC 2), second pass | 13 (1 major, 12 minor) | 2 (P1 quiz heading time, P4 leaked authoring sentence) | 11 minor, listed in `qc_report_2_instructional.md` |

Open items in total: 13, none critical. The most useful to fix next: the answer key still runs together in one paragraph; the Practice heading says 8 min while its activity token says 6 (raising the token to 8 fails the pacing gate at 48.1 min); Q1's wrong options are too obviously absurd; O3 (POST) is only lightly assessed in the quiz.

## What the process caught
- The code gate caught two gaps in the first fact-check that the agent's own report did not mention (a claim with a "partially supported" verdict but no evidence quote, and 6 items not covered), and sent it back; the second run passed.
- The independent pedagogy review found the quiz mostly repeated worked examples; three major issues were fixed (new scenarios for Q3 and Q5, more plausible wrong options).
- The final editor refused four suggested fixes because they would have added uncited or incorrect claims, and reverted one that broke the pacing gate.
- Three defects in the project's own tools were found and fixed during this run: the scraper cut RFC 9110 off before its method definitions (now relevance-trimmed, up to 700,000 characters read); the status-class check flagged deliberately wrong quiz options; the uncited-statement check flagged labelled examples and questions.

## Honest limits
- No source states plainly that "POST is unencrypted"; the lesson derives it from S5 and S8 (HTTPS protects both methods) and labels it the lesson's own synthesis.
- Status classes rest on MDN, Wikipedia, http.dev, Cloudflare and the Systems Approach book, because the RFC text fetched stops before its status-code section.
- The factual claims were verified by an AI fact-checker against source text, with the quotes re-checked by code. That is strong evidence, but an instructor should still read the lesson.
- Run folder: `runs/http-requests-and-responses-20261107-1724/` (intermediate files, both audit passes and the gate reports are kept there).
