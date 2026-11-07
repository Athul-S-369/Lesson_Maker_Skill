"""Markdown -> Word (.docx) for the final lesson deliverables.

    python -m app.docx_export <folder or file.md> [--sources sources.json] [--out <folder>]

Converts every *.md in a folder (or one file) to a .docx next to it: headings, paragraphs, bold/italic/inline code,
bullet and numbered lists (nested), blockquotes, fenced code blocks, tables (header row repeated, shaded),
hyperlinks (http/https only) and horizontal rules. Lesson-specific tokens are made readable:
`{{video:S17}}` becomes "Embedded video S17: <title> (link)" when sources.json is given, `[activity: 6 min]`
becomes a bold "Activity (6 min):". Raw HTML is never interpreted: text such as <protocol> stays literal.
"""
import json
import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from markdown_it import MarkdownIt

VIDEO_LINE = re.compile(r"(?m)^\{\{video:(S\d+)\}\}[ \t]*$")
ACTIVITY = re.compile(r"\[activity:\s*(\d+)\s*min\]", re.I)
BR = re.compile(r"<br\s*/?>", re.I)
MONO = "Consolas"
TABLE_PT, CODE_PT = 9, 9
HEADER_FILL, CODE_FILL, QUOTE_FILL = "D9E2F3", "F2F2F2", "F4FBF6"


def preprocess(md: str, sources: list[dict] | None = None) -> str:
    by_id = {s["id"]: s for s in sources or [] if isinstance(s, dict) and "id" in s}

    def video(m):
        s = by_id.get(m.group(1))
        if not s:
            return f"**Embedded video {m.group(1)}**"
        title = re.sub(r"[\[\]]", "", str(s.get("title", m.group(1))))
        return f"**Embedded video {m.group(1)}:** [{title}]({s.get('url', '')})"
    md = VIDEO_LINE.sub(video, md)
    return ACTIVITY.sub(lambda m: f"**Activity ({m.group(1)} min):**", md)


# ---------------- low-level Word helpers ----------------
def _shade(element_pr, fill: str) -> None:
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    element_pr.append(shd)


def _border(paragraph, side: str, color: str = "6CC08B", size: int = 18) -> None:
    pPr = paragraph._p.get_or_add_pPr()
    bdr = OxmlElement("w:pBdr")
    el = OxmlElement(f"w:{side}")
    el.set(qn("w:val"), "single")
    el.set(qn("w:sz"), str(size))
    el.set(qn("w:space"), "6")
    el.set(qn("w:color"), color)
    bdr.append(el)
    pPr.append(bdr)


def _hyperlink(paragraph, url: str, text: str, bold: bool, italic: bool, size: float | None) -> None:
    r_id = paragraph.part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink", is_external=True)
    h = OxmlElement("w:hyperlink")
    h.set(qn("r:id"), r_id)
    run = OxmlElement("w:r")
    rpr = OxmlElement("w:rPr")
    for tag, val in (("w:color", "0563C1"), ("w:u", "single")):
        e = OxmlElement(tag)
        e.set(qn("w:val"), val)
        rpr.append(e)
    if bold:
        rpr.append(OxmlElement("w:b"))
    if italic:
        rpr.append(OxmlElement("w:i"))
    if size:
        sz = OxmlElement("w:sz")
        sz.set(qn("w:val"), str(int(size * 2)))
        rpr.append(sz)
    run.append(rpr)
    t = OxmlElement("w:t")
    t.text = text
    t.set(qn("xml:space"), "preserve")
    run.append(t)
    h.append(run)
    paragraph._p.append(h)


def _run(paragraph, text: str, bold=False, italic=False, code=False, size: float | None = None):
    r = paragraph.add_run(text)
    r.bold = True if bold else None
    r.italic = True if italic else None
    if code:
        r.font.name = MONO
        r._element.rPr.rFonts.set(qn("w:eastAsia"), MONO)
        r.font.size = Pt(size or 10)
    elif size:
        r.font.size = Pt(size)
    return r


def add_inline(paragraph, children, size: float | None = None) -> None:
    """Render a markdown-it inline token list into runs (and hyperlinks) of `paragraph`."""
    bold = italic = 0
    link, link_text = None, []

    def emit(text: str, code: bool = False) -> None:
        if link is not None:
            link_text.append(text)
            return
        for k, part in enumerate(BR.split(text)):
            if k:
                paragraph.add_run().add_break()
            if part:
                _run(paragraph, part, bold > 0, italic > 0, code, size)

    for t in children or []:
        ty = t.type
        if ty == "strong_open":
            bold += 1
        elif ty == "strong_close":
            bold -= 1
        elif ty == "em_open":
            italic += 1
        elif ty == "em_close":
            italic -= 1
        elif ty == "link_open":
            link, link_text = t.attrGet("href") or "", []
        elif ty == "link_close":
            text = "".join(link_text) or (link or "")
            if re.match(r"https?://", link or "", re.I):
                _hyperlink(paragraph, link, text, bold > 0, italic > 0, size)
            else:                                        # never create a clickable javascript:/file: link
                _run(paragraph, text, bold > 0, italic > 0, False, size)
            link = None
        elif ty == "code_inline":
            emit(t.content, code=True)
        elif ty == "softbreak":
            emit(" ")
        elif ty == "hardbreak":
            paragraph.add_run().add_break()
        elif ty == "image":
            emit(t.content or "[image]")
        elif ty in ("text", "html_inline"):
            emit(t.content)


def _match(tokens, i: int) -> int:
    level = 0
    for k in range(i, len(tokens)):
        level += tokens[k].nesting
        if level == 0:
            return k
    return len(tokens) - 1


# ---------------- the converter ----------------
class _Builder:
    def __init__(self, doc):
        self.doc = doc

    def render(self, tokens, container=None, depth: int = 0, quote: bool = False) -> None:
        container = container if container is not None else self.doc
        i = 0
        while i < len(tokens):
            i = self.block(tokens, i, container, depth, quote)

    def block(self, tokens, i: int, container, depth: int, quote: bool) -> int:
        t = tokens[i]
        ty = t.type
        if ty == "heading_open":
            level = min(int(t.tag[1]), 4)
            p = container.add_paragraph(style=f"Heading {level}")
            add_inline(p, tokens[i + 1].children)
            return i + 3
        if ty == "paragraph_open":
            p = container.add_paragraph()
            add_inline(p, tokens[i + 1].children)
            if quote:
                self._quote(p)
            return i + 3
        if ty in ("bullet_list_open", "ordered_list_open"):
            return self.list_block(tokens, i, container, depth, ty == "ordered_list_open", quote)
        if ty == "blockquote_open":
            end = _match(tokens, i)
            self.render(tokens[i + 1:end], container, depth, quote=True)
            return end + 1
        if ty in ("fence", "code_block"):
            self._code(container, t.content)
            return i + 1
        if ty == "table_open":
            end = _match(tokens, i)
            self.table(tokens[i:end + 1], container)
            return end + 1
        if ty == "hr":
            p = container.add_paragraph()
            _border(p, "bottom", "999999", 6)
            return i + 1
        return i + 1                                    # html_block and unknown tokens: ignored (never interpreted)

    def _quote(self, p) -> None:
        p.paragraph_format.left_indent = Cm(0.8)
        _border(p, "left")
        _shade(p._p.get_or_add_pPr(), QUOTE_FILL)

    def _code(self, container, text: str) -> None:
        p = container.add_paragraph()
        p.paragraph_format.keep_together = True
        p.paragraph_format.left_indent = Cm(0.4)
        _shade(p._p.get_or_add_pPr(), CODE_FILL)
        lines = text.rstrip("\n").split("\n")
        for k, line in enumerate(lines):
            if k:
                p.add_run().add_break()
            _run(p, line, code=True, size=CODE_PT)

    def list_block(self, tokens, i: int, container, depth: int, ordered: bool, quote: bool) -> int:
        end = _match(tokens, i)
        j, n = i + 1, 0
        while j < end:
            if tokens[j].type == "list_item_open":
                k = _match(tokens, j)
                n += 1
                self.item(tokens[j + 1:k], container, depth, ordered, n, quote)
                j = k + 1
            else:
                j += 1
        return end + 1

    def item(self, toks, container, depth: int, ordered: bool, n: int, quote: bool) -> None:
        first, j = True, 0
        while j < len(toks):
            t = toks[j]
            if first:
                first = False
                p = self._list_paragraph(container, depth, ordered, n)
                if t.type == "paragraph_open":
                    add_inline(p, toks[j + 1].children)
                    j += 3
                    continue
            if t.type in ("bullet_list_open", "ordered_list_open"):
                j = self.list_block(toks, j, container, depth + 1, t.type == "ordered_list_open", quote)
            else:
                j = self.block(toks, j, container, depth + 1, quote)

    @staticmethod
    def _list_paragraph(container, depth: int, ordered: bool, n: int):
        if not ordered:
            return container.add_paragraph(style=("List Bullet", "List Bullet 2", "List Bullet 3")[min(depth, 2)])
        p = container.add_paragraph()
        p.paragraph_format.left_indent = Cm(0.9 * (depth + 1))
        p.paragraph_format.first_line_indent = Cm(-0.6)
        p.add_run(f"{n}. ")
        return p

    def table(self, toks, container) -> None:
        rows, cur = [], None
        for k, t in enumerate(toks):
            if t.type == "tr_open":
                cur = []
                rows.append((cur, False))
            elif t.type in ("th_open", "td_open"):
                cur.append(toks[k + 1].children if k + 1 < len(toks) and toks[k + 1].type == "inline" else [])
                if t.type == "th_open":
                    rows[-1] = (cur, True)
        if not rows:
            return
        cols = max(len(r) for r, _ in rows)
        table = container.add_table(rows=len(rows), cols=cols)
        table.style = "Table Grid"
        for ri, (cells, is_header) in enumerate(rows):
            for ci in range(cols):
                cell = table.cell(ri, ci)
                p = cell.paragraphs[0]
                add_inline(p, cells[ci] if ci < len(cells) else [], size=TABLE_PT)
                if is_header:
                    for r in p.runs:
                        r.bold = True
                    _shade(cell._tc.get_or_add_tcPr(), HEADER_FILL)
            if is_header:                               # repeat the header row on every page
                trPr = table.rows[ri]._tr.get_or_add_trPr()
                trPr.append(OxmlElement("w:tblHeader"))
        container.add_paragraph().paragraph_format.space_after = Pt(4)


def _page_number_footer(doc, label: str) -> None:
    p = doc.sections[0].footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(f"{label}   |   Page ")
    r.font.size = Pt(9)
    r.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
    run = p.add_run()
    run.font.size = Pt(9)
    for kind, text in (("begin", None), (None, "PAGE"), ("end", None)):
        if kind:
            el = OxmlElement("w:fldChar")
            el.set(qn("w:fldCharType"), kind)
        else:
            el = OxmlElement("w:instrText")
            el.set(qn("xml:space"), "preserve")
            el.text = text
        run._r.append(el)


def md_to_docx(md_text: str, out_path, sources: list[dict] | None = None, title: str | None = None):
    """Convert Markdown text to a Word document at `out_path`; returns the path."""
    out_path = Path(out_path)
    first_h1 = re.search(r"(?m)^#\s+(.+?)\s*$", md_text)
    title = title or (re.sub(r"[*_`]", "", first_h1.group(1)) if first_h1 else out_path.stem.replace("_", " "))
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(2.0)
    sec.top_margin = sec.bottom_margin = Cm(2.0)
    normal = doc.styles["Normal"]
    normal.font.name, normal.font.size = "Calibri", Pt(11)
    normal.paragraph_format.space_after = Pt(6)
    for lvl, size in ((1, 20), (2, 15), (3, 13), (4, 11.5)):
        h = doc.styles[f"Heading {lvl}"]
        h.font.name, h.font.size = "Calibri", Pt(size)
    doc.core_properties.title = title
    doc.core_properties.author = "hire-athul-lesson-maker"
    doc.core_properties.subject = "Generated from " + out_path.with_suffix(".md").name
    _page_number_footer(doc, title)
    md = MarkdownIt("commonmark", {"html": False}).enable("table")
    _Builder(doc).render(md.parse(preprocess(md_text, sources)))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out_path))
    return out_path


def _load_sources(path) -> list[dict]:
    if not path:
        return []
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    items = data.get("sources") if isinstance(data, dict) else data
    return [s for s in (items or []) if isinstance(s, dict)]


def convert(target, sources_path=None, out_dir=None) -> list[tuple[Path, Path]]:
    """Convert one .md file, or every .md file in a folder. Returns [(markdown path, docx path)]."""
    target = Path(target)
    files = [target] if target.is_file() else sorted(target.glob("*.md"))
    if not files:
        raise FileNotFoundError(f"No .md files found at {target}")
    sources = _load_sources(sources_path)
    out = []
    for f in files:
        dest = (Path(out_dir) if out_dir else f.parent) / (f.stem + ".docx")
        md_to_docx(f.read_text(encoding="utf-8"), dest, sources)
        out.append((f, dest))
    return out


def main(argv: list[str]) -> int:
    if not argv or argv[0].startswith("-"):
        print(__doc__)
        return 2
    opt = lambda name: argv[argv.index(name) + 1] if name in argv and argv.index(name) + 1 < len(argv) else None
    try:
        for md, docx in convert(argv[0], opt("--sources"), opt("--out")):
            print(f"{md.name} -> {docx}")
    except (OSError, ValueError, json.JSONDecodeError) as e:
        print(f"DOCX ERROR: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
