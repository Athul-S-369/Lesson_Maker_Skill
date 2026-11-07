# hire-athul-lesson-maker (shareable package)

A Claude Code,Cursor,Codex **skill** that builds a researched, source-cited, 45-minute lesson from a title and a learning objective, using a team of **12 specialised sub-agents** and a **deterministic code gate**. It needs **no API key**: the agents run on Claude Code's own models and research the web with a Scrapling-based scraper.

## Install (once)

1. Install Python 3.11+ and Claude Code.
2. In this folder run:
   ```
   python install.py
   ```
   This copies the skill to `~/.claude/skills/hire-athul-lesson-maker/`, the 12 agents to `~/.claude/agents/`, remembers where this folder is (the skill runs `app/gate.py` and `app/scraper.py` from here), and installs the Python packages. Keep this folder where it is.
3. Start a **new** Claude Code session (agents are loaded at session start).

## Use

```
/hire-athul-lesson-maker <lesson title> | <learning objective>
```

Optionally add `level: beginner|intermediate|advanced` and `mode: self_study|instructor_led`. Results appear in `runs/<lesson>-<timestamp>/final/`: `lesson.md`, `references.md`, `qc_report_1_factual.md`, `qc_report_2_instructional.md`, `summary.md` **and a Word version (`.docx`) of every one of them**, generated as the last step of the pipeline.

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
| kl-fact-checker                            | QC 1, independent, verbatim evidence quotes                  |
| kl-pedagogy-reviewer                       | QC 2, independent, outcome coverage matrix                   |
| kl-originality-editor                      | paraphrases copied passages                                  |
| kl-final-editor                            | applies verified fixes, re-gates, packages the deliverables  |

The gate (`python -m app.gate check <run_dir> --phase draft|audit`) re-checks what code can check: valid citations (never a video), plagiarism, measured 40-47 minutes, quiz key, required sections, and it re-verifies that **every evidence quote the fact-checker gives really occurs in its source**. Repair loops are limited to two passes and the gate is never loosened.

## Make Word documents from any Markdown
```
python -m app.docx_export <folder or file.md> [--sources sources.json] [--out <folder>]
```
Headings, bold/italic/code, nested lists, tables (shaded, repeating header row), code blocks, quotes and links are converted; the lesson's video and activity markers become readable text. The `.docx` files are always generated from the `.md` files: fix the `.md` and convert again instead of editing the Word file.

## Example output
`example/http-requests-and-responses/` holds the real deliverables of one run (lesson, references, both QC reports, summary; each as `.md` and `.docx`) so you can see what the skill produces. The scraped source texts of that run are not included.

## Limits (honest)

- The lesson is verified by an AI fact-checker against the source text, with the quotes re-checked by code. Strong evidence, but a human should still read it.
- Books are known only through pages that are legally readable online; author/publisher/year may be unverified.
- Keyless Bing search is a best-effort scrape and can change or block; the researchers fall back to WebSearch and direct URLs.
- Researched content is third-party material: credit the sources, which the skill lists in `references.md`.

## Credits

- github.com/Athul-S-369
