# File contracts of the hire-athul-lesson-maker pipeline

Every agent reads and writes files in the run directory `RUN` (`runs/<slug>-<timestamp>/`). All JSON is UTF-8. The deterministic gate (`python -X utf8 -m app.gate check RUN --phase draft|audit`) validates the files marked **gated**.

| File | Written by | Read by | Shape (abridged; each agent definition has the full schema) |
|---|---|---|---|
| `input.json` | orchestrator | planner | `{title, objective, level, mode, prerequisites}` |
| `plan.json` | kl-query-planner | most agents | `outcomes[{id,text,bloom}]`, `prerequisite_concepts`, `misconceptions`, `must_cover`, `queries{web[6],video[3],book[3]}` |
| `candidates_*.json` | kl-source-researcher, kl-video-curator | relevance judge, validator | `candidates[{type,title,url,published,snippet,text,...}]`, `failed[]` |
| `relevance.json` | kl-relevance-judge | validator, orchestrator | `scores[{url,relevance 0-10,covers,best_passage}]`, `keep[]`, `gaps[{outcome,suggested_query}]` |
| `sources.json` **gated** | kl-source-validator | everyone downstream, gate | `sources[{id S1..,type web|book|video,title,url,text,reliability{tier,score,rationale},injection_flags,...}]`, `corroboration[]`, `conflicts[]` |
| `outline.json` | kl-lesson-architect | writer, assessment designer | `sections[{heading,minutes,word_budget,teaches,sources}]`, `video`, `activity`, `quiz_plan`, `coverage`, `total_minutes` (42-46) |
| `lesson.md` **gated** | kl-lesson-writer, kl-assessment-designer, editors | auditors, gate | Markdown with `[Sx]` citations, `{{video:Sx}}`, `[activity: N min]`, a Knowledge check with `**Answers:**` |
| `factcheck.json` **gated** | kl-fact-checker | gate, final editor | `claims[{claim,quote,cited,kind,verdict,evidence_quote,confidence}]`, `issues[{id,severity,category,quote,problem,replacement,status}]` |
| `pedagogy.json` **gated** | kl-pedagogy-reviewer | gate, final editor | `objective_outcomes[{id,taught,practiced,assessed,where}]`, `dimensions{name:{score,comment}}`, `issues[]` |
| `gate_report.json` | code (`app.gate`) | orchestrator, writer, editors | `verdict PASS|FAIL`, `checks[{id,name,status,blocker,detail,fix}]`, `next_actions[]` |
| `final/*.md` | kl-final-editor | user | `lesson.md`, `references.md`, `qc_report_1_factual.md`, `qc_report_2_instructional.md`, `summary.md` |
| `final/*.docx` | code (`app.docx_export`, phase 9) | user | one Word file per `.md` above, generated from it (never edited by hand) |

## Gate checks (blocking unless marked warn)
`schema`, `source_count` (>= 3 text sources), `source_mix` (warn), `source_text` (warn), `citations` (ids exist, none a video), `uncited` (blocking above 3), `status_classes`, `injection` (warn), `originality` (>= 10% verbatim or a 25-word copied run blocks), `pacing` (40-47 measured min), `activity` (warn), `structure` (Knowledge check and Practice block), `video_tokens`, `quiz` (>= 3 questions, full key), `references` (warn).
Audit phase adds: `evidence` (every evidence quote must occur in its cited source), `coverage` (>= 90% of cited sentences and quiz answers fact-checked), `contradictions`, `support` (>= 80% supported), `fact_issues`, `coverage_matrix` (every outcome taught, practised, assessed), `pedagogy_issues`, `dimensions` (warn).

## Ids and tokens
Source ids are final once `sources.json` is written; nothing may renumber them. Videos are never cited for facts; they appear only as `{{video:Sx}}`.
