# File contracts of the hire-athul-lesson-maker pipeline (fast mode)

Every agent reads and writes files in the run directory `RUN` (`runs/<slug>-<timestamp>/`). All JSON is UTF-8. Scripts: `T` = `python -X utf8 -m app.lessontools`. The deterministic gate is `python -X utf8 -m app.gate check RUN --phase draft|audit`.

| File | Written by | Read by | Shape (abridged; each agent definition has the full schema) |
|---|---|---|---|
| `input.json` | orchestrator | planner | `{title, objective, level, mode, prerequisites}` |
| `plan.json` | kl-query-planner | most agents | `outcomes[{id,text,bloom}]`, `prerequisite_concepts`, `misconceptions`, `must_cover`, `queries{web[6],video[3],book[3]}` |
| `pages/*.txt` | scraper `--save` | digest, assemble | extracted page text, one file per page |
| `candidates_*.json` | kl-source-researcher, kl-video-curator | `T digest`, `T assemble` | `candidates[{type,title,url,published,snippet,text_file,...}]`, `failed[]` (no page text inline) |
| `digest.json` | `T digest` | relevance judge, validator | per candidate: `cand_id,type,title,url,published,chars,description_only,head,best_passages` |
| `relevance.json` | kl-relevance-judge | `T assemble`, orchestrator | scores keyed by `cand_id` (0-10), coverage, `gaps[{outcome,suggested_query}]` |
| `validation.json` | kl-source-validator | `T assemble` | `validation[]` (tier, score, rationale, flags per `cand_id`), `corroboration[]` (cand_ids + verbatim quotes), `conflicts[]`, `problems` |
| `sources.json` **gated** | `T assemble` | gate, fact-checkers, editors | `sources[{id S1..,type,title,url,text,reliability{tier,score,rationale},injection_flags}]`, `corroboration[]`, `conflicts[]`, `rejected[]`, `ok` |
| `source_excerpts.json` | `T excerpts` | architect, writer, assessment designer | per source: title, tier, caveats, relevant passages; plus corroboration and conflicts |
| `outline.json` | kl-lesson-architect | writer, assessment designer | `sections[{heading,minutes,word_budget,teaches,sources}]`, `video`, `activity`, `quiz_plan`, `coverage`, `hedge_or_omit`, `total_minutes` (42-46) |
| `lesson.md` **gated** | writer, assessment designer, fixes | auditors, gate | Markdown with `[Sx]` citations, `{{video:Sx}}`, `[activity: N min]`, `<<QUIZ>>` then a Knowledge check with `**Answers:**` |
| `factcheck_todo_<k>.json` | `T worklist` | fact-checker shard k | items `{quote, claim, cited, kind, evidence passages}` + output file name |
| `factcheck_shard_<k>.json` | kl-fact-checker | `T merge` | `claims[]`, `issues[]` for its items |
| `factcheck.json` **gated** | `T merge` | gate, `T apply-fixes` | merged `claims[{claim,quote,cited,kind,verdict,evidence_quote,confidence}]`, `issues[{id,severity,category,quote,problem,replacement,confidence,status}]` |
| `pedagogy.json` **gated** | kl-pedagogy-reviewer | gate, `T apply-fixes` | `objective_outcomes[{id,taught,practiced,assessed,where}]`, `dimensions{name:{score,comment}}`, `issues[]` |
| `fixes_report.json` | `T apply-fixes` | orchestrator, final editor | per issue: `applied` / `needs_human` and the reason |
| `gate_report.json` | code (`app.gate`) | orchestrator, writer, editors | `verdict PASS|FAIL`, `checks[{id,name,status,blocker,detail,fix}]`, `next_actions[]` |
| `timeline.json` | `T stamp` | `T package` | label to timestamp |
| `final/*.md` | `T package` | user | `lesson.md`, `references.md`, `qc_report_1_factual.md`, `qc_report_2_instructional.md`, `summary.md` (with timing table) |
| `final/*.docx` | `T package` (via `app.docx_export`) | user | one Word file per `.md` above, generated from it (never edit by hand) |

## Script commands
`T digest RUN` | `T assemble RUN` | `T excerpts RUN` | `T worklist RUN [--shards N]` | `T merge RUN` | `T apply-fixes RUN` | `T package RUN [--no-docx]` | `T stamp RUN <label>`.

`apply-fixes` applies an issue only if its quote occurs exactly once, a replacement is given, confidence >= 0.6, no `[Sx]` token or number disappears, cited ids exist and are not videos, no new uncited statement appears, pacing stays inside 40-47 minutes and no new gate blocker appears. Everything else is marked `needs_human`.

## Gate checks (blocking unless marked warn)
`schema`, `source_count` (>= 3 text sources), `source_mix` (warn), `source_text` (warn), `citations` (ids exist, none a video), `uncited` (blocking above 3), `status_classes`, `injection` (warn), `originality` (>= 10% verbatim or a 25-word copied run blocks), `pacing` (40-47 measured min), `activity` (warn), `structure` (Knowledge check and Practice block), `video_tokens`, `quiz` (>= 3 questions, full key), `references` (warn).
Audit phase adds: `evidence` (every evidence quote must occur in its cited source), `coverage` (>= 90% of cited sentences and quiz answers fact-checked), `contradictions`, `support` (>= 80% supported), `fact_issues`, `coverage_matrix` (every outcome taught, practised, assessed), `pedagogy_issues`, `dimensions` (warn).

## Ids and tokens
Source ids are final once `sources.json` is written; nothing may renumber them. Videos are never cited for facts; they appear only as `{{video:Sx}}`.
