#!/usr/bin/env python3
"""Render extras/cheat-sheet.md as a compact two-column A4 revision sheet.

This is a companion to the main book build, not part of it: the combined
manuscript is unaffected. Requires reportlab in the same environment used by
build_pdf.py.

    .venv/bin/python java-backend-interview-book/scripts/build_cheatsheet.py
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate, Paragraph,
                                Spacer)

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "extras" / "cheat-sheet.md"
TARGET = ROOT / "Java_Backend_Top_40_Cheat_Sheet.pdf"

BODY_FONT = "Helvetica"
BOLD_FONT = "Helvetica-Bold"
CODE_FONT = "Courier"
ACCENT = colors.HexColor("#1F4E79")
ACCENT_LIGHT = colors.HexColor("#2E75B6")
RULE = colors.HexColor("#C9D2DA")

MARGIN_X = 13 * mm
MARGIN_TOP = 12 * mm
MARGIN_BOTTOM = 13 * mm
GUTTER = 7 * mm

BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
ITALIC_RE = re.compile(r"(?<!\*)\*([^*]+?)\*(?!\*)")


def inline(text: str) -> str:
    """Markdown inline spans to ReportLab mini-HTML (same subset as the book)."""
    parts = text.split("`")
    out: list[str] = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            out.append(f'<font face="{CODE_FONT}" size="6.6">{html.escape(part)}</font>')
            continue
        chunk = html.escape(part)
        chunk = BOLD_RE.sub(lambda m: f"<b>{m.group(1)}</b>", chunk)
        chunk = ITALIC_RE.sub(lambda m: f"<i>{m.group(1)}</i>", chunk)
        out.append(chunk)
    return "".join(out)


def check_ascii(text: str) -> None:
    """The built-in Type 1 fonts cannot render arbitrary Unicode; fail loudly."""
    allowed = {"\u2014", "\u2013"}
    bad = sorted({c for c in text if ord(c) > 127} - allowed)
    if bad:
        names = ", ".join(f"U+{ord(c):04X} {c!r}" for c in bad)
        sys.exit(f"unsupported characters for the built-in fonts: {names}")


def build_styles() -> dict[str, ParagraphStyle]:
    return {
        "title": ParagraphStyle("title", fontName=BOLD_FONT, fontSize=15.5, leading=18,
                                textColor=ACCENT, spaceAfter=2),
        "subtitle": ParagraphStyle("subtitle", fontName=BODY_FONT, fontSize=7.9, leading=10.6,
                                   textColor=colors.HexColor("#40566B"), spaceAfter=5,
                                   alignment=TA_JUSTIFY),
        "callout": ParagraphStyle("callout", fontName=BODY_FONT, fontSize=8.2, leading=11,
                                  textColor=colors.HexColor("#14202B"), spaceAfter=7,
                                  borderWidth=0.7, borderColor=ACCENT_LIGHT, borderPadding=4,
                                  backColor=colors.HexColor("#EEF3F9")),
        "group": ParagraphStyle("group", fontName=BOLD_FONT, fontSize=8.6, leading=10.6,
                                textColor=ACCENT, spaceBefore=6.5, spaceAfter=2.6,
                                keepWithNext=True),
        # Ragged right: a 90 mm column plus long code tokens makes justified
        # text open up ugly gaps, so left alignment reads better here.
        "entry": ParagraphStyle("entry", fontName=BODY_FONT, fontSize=7.35, leading=9.3,
                                textColor=colors.HexColor("#1A1A1A"), spaceAfter=3.9,
                                alignment=TA_LEFT),
    }


def parse(md: str) -> tuple[str, list[str], list[tuple[str, list[str]]]]:
    """Split the source into title, intro paragraphs and (group, entries)."""
    title = ""
    intro: list[str] = []
    groups: list[tuple[str, list[str]]] = []
    for raw in md.splitlines():
        line = raw.rstrip()
        if line.startswith("# "):
            title = line[2:].strip()
        elif line.startswith("## "):
            groups.append((line[3:].strip(), []))
        elif line.startswith("- "):
            if not groups:
                sys.exit("entry found before any group heading")
            groups[-1][1].append(line[2:].strip())
        elif line:
            intro.append(line)
    if not title or not groups:
        sys.exit("cheat-sheet.md is missing its title or groups")
    return title, intro, groups


def footer(canvas, doc) -> None:
    canvas.saveState()
    width, _ = A4
    y = MARGIN_BOTTOM - 4 * mm
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.4)
    canvas.line(MARGIN_X, y + 3.2 * mm, width - MARGIN_X, y + 3.2 * mm)
    canvas.setFont(BODY_FONT, 6.8)
    canvas.setFillColor(colors.HexColor("#6B7B8C"))
    canvas.drawString(MARGIN_X, y, "Top 200 Java Backend Developer Interview Questions "
                                   "- Top 40 cheat sheet")
    canvas.drawRightString(width - MARGIN_X, y, f"Page {canvas.getPageNumber()}")
    canvas.restoreState()


def main() -> int:
    if not SOURCE.exists():
        sys.exit(f"missing source: {SOURCE}")
    md = SOURCE.read_text(encoding="utf-8")
    check_ascii(md)
    title, intro, groups = parse(md)
    styles = build_styles()

    width, height = A4
    col_w = (width - 2 * MARGIN_X - GUTTER) / 2
    col_h = height - MARGIN_TOP - MARGIN_BOTTOM
    frames = [
        Frame(MARGIN_X, MARGIN_BOTTOM, col_w, col_h, id="left",
              leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0),
        Frame(MARGIN_X + col_w + GUTTER, MARGIN_BOTTOM, col_w, col_h, id="right",
              leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0),
    ]
    doc = BaseDocTemplate(str(TARGET), pagesize=A4, title=title,
                          author="Java backend interview preparation",
                          leftMargin=MARGIN_X, rightMargin=MARGIN_X,
                          topMargin=MARGIN_TOP, bottomMargin=MARGIN_BOTTOM)
    doc.addPageTemplates([PageTemplate(id="two-col", frames=frames, onPage=footer)])

    story = [Paragraph(inline(title), styles["title"])]
    for i, para in enumerate(intro):
        style = "callout" if para.startswith("**If you only") else "subtitle"
        story.append(Paragraph(inline(para), styles[style]))
        if i == 0:
            story.append(Spacer(1, 1))
    entries = 0
    for name, items in groups:
        story.append(Paragraph(inline(name), styles["group"]))
        for item in items:
            story.append(Paragraph(inline(item), styles["entry"]))
            entries += 1

    doc.build(story)
    size = TARGET.stat().st_size
    print(f"wrote {TARGET.relative_to(ROOT.parent)}")
    print(f"  entries={entries} bytes={size:,}")
    if entries != 40:
        sys.exit(f"expected 40 entries, found {entries}")
    return verify(entries)


def verify(entries: int) -> int:
    """Read the PDF back and confirm it carries the same IDs as top-40.md."""
    try:
        import pypdf
    except ImportError:
        print("  note: pypdf not installed, skipped the read-back check")
        return 0

    reader = pypdf.PdfReader(str(TARGET))
    pages = len(reader.pages)
    text = "\n".join((page.extract_text() or "") for page in reader.pages)
    found = set(re.findall(r"Q\d{3}", text))

    top40 = ROOT / "extras" / "top-40.md"
    expected = set(re.findall(r"^\|\s*(Q\d{3})\s*\|", top40.read_text(encoding="utf-8"), re.M))

    failures = []
    if pages < 1 or pages > 2:
        failures.append(f"expected 1-2 pages, got {pages}")
    if len(expected) != 40:
        failures.append(f"top-40.md lists {len(expected)} ids, expected 40")
    missing = sorted(expected - found)
    if missing:
        failures.append(f"ids in top-40.md but not on the sheet: {', '.join(missing)}")
    extra = sorted(found - expected)
    if extra:
        failures.append(f"ids on the sheet that are not in top-40.md: {', '.join(extra)}")

    print(f"  pages={pages} ids_matched={len(expected & found)}/40")
    for problem in failures:
        print(f"  FAIL  {problem}")
    if failures:
        return 1
    print("  RESULT: PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
