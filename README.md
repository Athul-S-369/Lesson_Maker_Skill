# hire-athul-lesson-maker (shareable package)

A Claude Code,Cursor,Codex **skill** that builds a researched, source-cited, 45-minute lesson from a title and a learning objective, using a team of **12 specialised sub-agents** and a **deterministic code gate**. It needs **no API key**: the agents run on Claude Code's own models and research the web with a Scrapling-based scraper.

## Install (once)

1. Install Python 3.11+ and Claude Code.
2. In this folder run:
   ```
   python install.py
   ```
   This copies the skill to `~/.claude/skills/hire-athul-lesson-maker/`, the 12 agents to `~/.claude/agents/`, remembers where this folder is (the skill runs `app/gate.py`, `app/scraper.py` and `app/lessontools.py` from here), and installs the Python packages. Keep this folder where it is.
3. Start a **new** Claude Code session (agents are loaded at session start).

## Use

```
/hire-athul-lesson-maker <lesson title> | <learning objective>
```

Optionally add `level: beginner|intermediate|advanced` and `mode: self_study|instructor_led`. Results appear in `runs/<lesson>-<timestamp>/final/`: `lesson.md`, `references.md`, `qc_report_1_factual.md`, `qc_report_2_instructional.md`, `summary.md` **and a Word version (`.docx`) of every one of them**, built by the final `package` script.

## How it works

| Agent                                      | Job                                                          |
| ------------------------------------------ | ------------------------------------------------------------ |
| kl-query-planner                           | outcomes, misconceptions, must-cover facts, search queries   |
| kl-source-researcher (several in parallel) | finds and scrapes web and book sources                       |
| kl-video-curator                           | YouTube candidates, duration, transcripts                    |
| kl-relevance-judge                         | scores sources against the outcomes, finds gaps              |
| kl-source-validator                        | authority, recency, corroboration, injection scan, final ids |
| kl-lesson-architect                        | 45-minute blueprint with word budgets                        |
| kl-lesson-writer                           | writes from the sources only (no web access)                 |
| kl-assessment-designer                     | knowledge check with a sourced answer key                    |
| kl-fact-checker (3 shards in parallel)     | QC 1, independent, verbatim evidence quotes                  |
| kl-pedagogy-reviewer                       | QC 2, independent, outcome coverage matrix                   |
| kl-originality-editor                      | paraphrases copied passages                                  |
| kl-final-editor                            | escalation only: fixes the few issues the scripts cannot     |

The gate (`python -m app.gate check <run_dir> --phase draft|audit`) re-checks what code can check: valid citations (never a video), plagiarism, measured 40-47 minutes, quiz key, required sections, and it re-verifies that **every evidence quote the fact-checker gives really occurs in its source**. Repair loops are limited to two passes and the gate is never loosened.

## Fast mode (what makes it quick)

Agents judge; scripts (`python -m app.lessontools ...`) type, merge and package. Scraped pages are saved to disk and never copied through agents; judges read a small digest; the writer reads relevant excerpts instead of whole pages; the fact-check runs as three parallel shards over pre-extracted claims with their evidence passages; safe fixes are applied by code, and the final files and Word documents are built by code. Every check stays the same, so the gate still decides PASS or FAIL. The `final/summary.md` of each run has a timing table.

## Make Word documents from any Markdown
```
python -m app.docx_export <folder or file.md> [--sources sources.json] [--out <folder>]
```
Headings, bold/italic/code, nested lists, tables (shaded, repeating header row), code blocks, quotes and links are converted; the lesson's video and activity markers become readable text. The `.docx` files are always generated from the `.md` files: fix the `.md` and convert again instead of editing the Word file.

## Try the gate without running anything

`example/http-requests-and-responses/` is a complete finished run (sources, lesson, both audits, final deliverables). Check it yourself:

```
python -m app.gate check example/http-requests-and-responses --phase audit
```

It should print `GATE PASS (audit)`.

## Limits (honest)

- The lesson is verified by an AI fact-checker against the source text, with the quotes re-checked by code. Strong evidence, but a human should still read it.
- Books are known only through pages that are legally readable online; author/publisher/year may be unverified.
- Keyless Bing search is a best-effort scrape and can change or block; the researchers fall back to WebSearch and direct URLs.
- Researched content is third-party material: credit the sources, which the skill lists in `references.md`.

## Credits

- github.com/Athul-S-369
