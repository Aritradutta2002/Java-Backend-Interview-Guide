#!/usr/bin/env python3
"""Verify the generated PDF: it exists, is non-empty, parses, and contains the book.

    .venv/bin/python java-backend-interview-book/scripts/verify_pdf.py

Checks
  1. The file exists and is larger than 100 KB.
  2. pypdf can parse it and report a page count above 100.
  3. Extracted text contains the title, Q001, Q100, Q200 and every chapter heading.
  4. The document has outline bookmarks and internal contents links.
  5. Every question heading Q001..Q200 is found in the extracted text.

Exit code is non-zero if any check fails.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover - environment guidance
    sys.exit("pypdf is required: python3 -m venv .venv && .venv/bin/pip install reportlab pypdf")

ROOT = Path(__file__).resolve().parent.parent
PDF = ROOT / "Java_Backend_Top_200_Interview_Questions.pdf"

def chapter_titles() -> list[str]:
    """Chapter headings, read from the sources so the check cannot drift."""
    return [path.read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip()
            for path in sorted((ROOT / "chapters").glob("*.md"))]



failures: list[str] = []
notes: list[str] = []


def check(condition: bool, message: str) -> None:
    if condition:
        notes.append(f"  PASS  {message}")
    else:
        failures.append(f"  FAIL  {message}")


def main() -> int:
    if not PDF.exists():
        print(f"  FAIL  {PDF} does not exist; run scripts/build_pdf.py")
        return 1
    size = PDF.stat().st_size
    check(size > 100_000, f"PDF exists and is {size:,} bytes.")

    reader = PdfReader(str(PDF))
    pages = len(reader.pages)
    check(pages > 100, f"PDF parses with pypdf: {pages} pages.")

    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    normalised = re.sub(r"[ \t]+", " ", text)

    check("Top 200 Java Backend Developer" in normalised, "Title page text present.")
    for marker in ("Q001.", "Q100.", "Q200."):
        check(marker in normalised, f"Extracted text contains {marker}")

    found = {m.group(1) for m in re.finditer(r"\b(Q\d{3})\.", normalised)}
    missing = [f"Q{n:03d}" for n in range(1, 201) if f"Q{n:03d}" not in found]
    check(not missing, f"All 200 question IDs appear in the extracted text"
                       + (f" (missing: {missing[:8]})" if missing else "."))

    titles = chapter_titles()
    check(len(titles) == 10, f"Found {len(titles)} chapter source files.")
    for title in titles:
        compact = re.sub(r"\s+", " ", title)
        check(compact in normalised, f"Chapter heading present: {compact[:48]}...")

    try:
        outline = reader.outline
        count = sum(1 for _ in _flatten(outline))
    except Exception as exc:  # pragma: no cover - defensive
        outline, count = [], 0
        notes.append(f"  note  outline could not be read: {exc}")
    check(count >= 200, f"PDF outline contains {count} bookmarks.")

    links = 0
    for page in reader.pages:
        for annot in page.get("/Annots", []) or []:
            obj = annot.get_object()
            if obj.get("/Subtype") == "/Link":
                links += 1
    check(links >= 200, f"PDF contains {links} link annotations (clickable contents).")

    for line in notes:
        print(line)
    for line in failures:
        print(line)
    print("-" * 72)
    print(f"checks={len(notes) + len(failures)} failures={len(failures)}")
    print("RESULT: PASSED" if not failures else "RESULT: FAILED")
    return 1 if failures else 0


def _flatten(items):
    for item in items:
        if isinstance(item, list):
            yield from _flatten(item)
        else:
            yield item


if __name__ == "__main__":
    raise SystemExit(main())
