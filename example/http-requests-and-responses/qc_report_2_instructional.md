# QC report 2: instructional quality

Source: second-pass `pedagogy.json` (the first pass is kept in `pedagogy_pass1.json`). Pacing from `gate_report.json`.

## Coverage matrix

| ID | Outcome | Taught | Practised | Assessed | Where | Note |
|---|---|---|---|---|---|---|
| O1 | Describe the structure of an HTTP request and response (start line, headers, optional body) as the context in which methods and status codes appear. | yes | yes | yes | Taught: Section 2 (four-part shape, request line, status line, annotated GET /contact exchange). Practiced: Practice Step 1 (annotate POST /orders from section 4). Assessed: Knowledge check Q1. | Q1 checks only response anatomy (status line, blank line, body). The request line (method, target, version) is practised in Step 1 but never assessed. Q1 distractors (a) and (c) are still implausible. |
| O2 | Explain the purpose of the GET method, including where its data travels (URL/query string) and its safe and idempotent semantics. | yes | yes | yes | Taught: Section 3 (query string, safe, idempotent, cacheable, bookmarkable). Practiced: Practice items A and C; key A now models 'safe and idempotent'. Assessed: Knowledge check Q2 option (a) and Q3 (query string, read-only). | Now adequately covered. Q3 adds a transfer check on query-string data and read-only use. Safe and idempotent are assessed only inside the compound Q2 (a). |
| O3 | Explain the purpose of the POST method, including where its data travels (request body) and why it is not idempotent or safe. | yes | yes | yes | Taught: Section 4 (body, Content-Type, POST /orders 201 example, ord_1001/ord_1002 repeat, not safe, not idempotent, retry caution). Practiced: Practice items B and D, Step 1 annotation of the POST body, and the G extra sentence on duplicate orders. Assessed: Knowledge check Q2 option (a) ('repeating a POST may repeat its effect'). | Assessment got thinner in this revision. The old Q5 (503 on POST, duplicate on retry) was replaced, so O3 now rests on one clause of Q2 (a). POST's body location and the fact that it is not safe are still never assessed. See P8. |
| O4 | Choose GET or POST for a given scenario and justify the choice. | yes | yes | yes | Taught: Section 4 comparison table and 'Choose with three questions'. Practiced: Practice Step 2, items A-D, with the remediation pointer to section 4. Assessed: Knowledge check Q3 (recipe filter). | Fixed since pass 1. Q3 is a new scenario, so the learner has to apply the 'read-only, shareable' question rather than recall a worked answer. Distractor (c) is weak, but (a) targets a real misconception. |
| O5 | Distinguish 2xx, 4xx, and 5xx status categories by what each says about who or what is responsible for the outcome. | yes | yes | yes | Taught: Section 5 class table ('Who is responsible' column) and the 'who must change something' heuristic. Practiced: Practice Step 3, items E-I. Assessed: Knowledge check Q4 and Q5. | Q4 (c) is now a plausible misconception distractor ('4xx and 5xx both mean the request was faulty'). Practice key entries F, H and I still do not state who is responsible, although Step 3 asks for it. |
| O6 | Classify specific status codes and request/response exchanges into the 2xx, 4xx, or 5xx category and name the likely next action (for example, fix the request or retry later). | yes | yes | yes | Taught: Section 5 (per-code explanations, 'Retrying needs care', full POST /orders 503 exchange). Practiced: Practice Step 3, items E-I, with the remediation pointer to section 5. Assessed: Knowledge check Q5 (POST /orders returning 400, malformed body). | Q5 is now an unseen exchange that asks for a 4xx next action, and the key (b) with [S6, S12] is consistent. The quiz no longer asks for a 5xx next action ('retry later'), so that half of O6 is practised (G, I) but not assessed. See P11. |

Gate coverage_matrix check: pass (6 outcomes).

## Dimension scores (1-5)

| Dimension | Score | Comment |
|---|---|---|
| objective_alignment | 4 | Every outcome is taught, practised and assessed, and O4 and O6 now use transfer items (Q3 recipe filter, Q5 400 on POST /orders), but O3 assessment shrank to one clause of Q2 (a) and the 5xx next action is no longer quizzed. |
| clarity | 3 | The explanations are precise, but 'The next two sentences synthesize S5 and S8.' still leaks authoring text, '(rule: ...)' tags remain, and the Section 5 lead-in still says 'one new line' above a full exchange. |
| structure | 4 | The arc from hook to anatomy, GET, POST, choosing, status codes, video, practice, quiz and wrap-up is sound and the practice remediation pointer now maps items to sections, but the answer key is still one run-on paragraph directly under the questions, and two section time labels disagree with what the sections take. |
| examples | 5 | Concrete raw exchanges for GET 200, GET 404, POST 201 and now a full POST /orders 503 with Retry-After, all reused in the practice and quiz. |
| practical_application | 4 | The triage desk is well scaffolded, with timed steps, a covered key and a working A-D / E-I remediation pointer, but key entries F, H and I omit the 'who is responsible' field that Step 3 asks learners to write. |
| assessment_quality | 4 | Q3, Q4 (c) and Q5 are clear improvements, testing transfer and real misconceptions, but Q1 distractors are still giveaways, Q2 bundles O2 and O3 in one option, and the 5xx next action and POST's body and unsafe properties are untested. |
| level_fit | 4 | The brief prerequisite definitions suit an intermediate self-study learner with empty prerequisites, and the 408/429 aside is now flagged as a side note, though the protocol-version aside and the untimestamped video skip instructions still add friction. |

Note: these scores were given before the release pass. The clarity comment mentions the leaked sentence, which has since been removed (P4). The scores were not re-rated.

Gate dimensions check: pass.

## Pacing

- Measured duration (gate, audit phase): **46.0 min**, against an allowed range of 40-47 min. Check status: pass.
- Section time labels in the final lesson:

  - 1. Hook and objective: about 2.5 min
  - 2. Anatomy of a request and a response: about 4 min
  - 3. GET: asking for a representation: about 5 min
  - 4. POST: submitting data, and choosing between GET and POST: about 7 min
  - 5. Status codes: 2xx, 4xx and 5xx: about 6 min
  - Watch and notice: about 5 min
  - Practice: about 8 min
  - Knowledge check: about 9 min
  - Wrap-up: about 2 min

- The labels add up to 48.5 min. After the P1 relabel (Knowledge check 5 -> 9 min), the labels promise more time than the measured 46.0 min and more than the 47-min ceiling. Part of the gap is the open P2 mismatch: Practice is labelled 8 min while its activity token says 6 min. The P1 suggestion to recover time by cutting prose was not applied.

## Issues (second pass)

| ID | Severity | Category | Status | Problem | Replacement offered |
|---|---|---|---|---|---|
| P1 | major | pacing | applied | The knowledge check measures about 9 minutes (five scenario MCQs, a code block and a dense explanatory key), almost twice the 'about 5 min' label. A self-study learner planning by headings will run about 4 minutes over at the end. The heading labels sum to 44.5 min while the lesson measures 46.0 of the 47 allowed, so there is no slack to absorb the gap by adding content elsewhere. | yes |
| P2 | minor | pacing | open | The heading says 'Practice (about 8 min)' while the token says '[activity: 6 min]', and the step budgets (1 + 2 + 3) add up to 6. The missing 2 minutes are never assigned, so the learner sees two conflicting numbers. Pass 1 found that raising the token to 8 min breaks the gate (48.1 min), so the fix should explain the gap instead of changing the token. | yes |
| P3 | minor | structure | open | All five answers still run together in one paragraph directly under Q5, with no sentence breaks between items and no instruction to answer first. A self-study learner can easily see answers by accident and has trouble finding one answer. There is also no remediation pointer for missed quiz items, unlike the practice. | yes |
| P4 | minor | clarity | applied | Authoring and provenance text has leaked into learner-facing prose. It means nothing to the learner and breaks the flow of the key security misconception passage. | yes |
| P5 | minor | clarity | open | Internal '(rule: ...)' and '(rules: ...)' labels remain in example lead-ins. They also appear as '(rule: a missing resource gets 404 [S9, S14])', '(rule: [S1, S6])', '(rules: [S6, S1])' and '(rules: [S6, S12, S1])'. They read as authoring scaffolding and add noise for a self-study reader. | yes |
| P6 | minor | clarity | open | The code block below this sentence now shows a full request and response (POST /orders with body, then 503 with Retry-After), not 'one new line'. The lead-in no longer matches the example. | yes |
| P7 | minor | practical_application | open | Step 3 asks for 'the class, who is responsible and the next action', but key entries F, H and I give no responsible party ('success', 'permissions', 'gateway trouble'). Learners cannot fully self-check the O5 skill. This rewrite uses only wording already in the section 5 class table, to avoid the citation concern that blocked the pass-1 fix. | yes |
| P8 | minor | assessment | open | Q2 still bundles O2 and O3 in one correct option, so a miss cannot be traced to either method. Since Q5 was replaced, this clause is the only quiz evidence for O3, and POST's body location and the fact that it is not safe are never assessed. | yes |
| P9 | minor | assessment | open | Distractors (a) and (c) are not plausible ('the body starts at the first line', 'status code is in the last line'). A learner who skipped section 2 can still rule them out, so Q1 does not show O1 understanding. | yes |
| P10 | minor | assessment | open | O1 covers requests and responses, but Q1 tests only the response. The request line (method, target, version) is practised in Step 1 but never assessed. | no |
| P11 | minor | assessment | open | O6 asks for the likely next action. With the old 503 Q5 gone, the quiz assesses the 4xx next action (Q5) but never the 5xx next action ('retry later'). Q4's correct option assigns blame but no action. | yes |
| P12 | minor | level_fit | open | This aside about unnamed newer protocol versions serves no outcome. It raises a question the lesson never answers, in a section whose job is anatomy. Removing it also frees a little time toward the pacing gap in P1. | yes |
| P13 | minor | level_fit | open | In self-study mode the learner has no timestamps, so 'skip ... passages' and 'pause before the signup challenge is answered' cannot be followed efficiently inside a 5-minute block. | no |

Applied in the release pass: P1 (heading relabelled) and P4 (meta sentence deleted). All other issues stay open as instructed; none was applied.

## First pass

The first pass (pedagogy_pass1.json) found 3 major issues, all in the knowledge check: P1 (Q5 repeated the worked 503 example), P2 (the only O4 item repeated the login answer) and P3 (implausible distractors). Of its 16 issues, 8 were applied (P1, P2, P3, P7, P8, P10, P11, P15). The other 8 were marked `needs_human` (P4, P5, P6, P9, P12, P13, P14, P16).
