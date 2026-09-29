#!/usr/bin/env python3
"""Assemble the single-file Markdown manuscript from the chapter and extras sources.

Pure standard library. Run from anywhere:

    python3 java-backend-interview-book/scripts/build_book.py

Output: java-backend-interview-book/Java_Backend_Top_200_Interview_Questions.md

The combined file is generated, never edited by hand: every chapter and extras
file is the single source of truth for its own content. The script adds the
title block, a linked table of contents and the chapter ordering.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "Java_Backend_Top_200_Interview_Questions.md"

TITLE = "Top 200 Java Backend Developer Interview Questions and Answers"
SUBTITLE = "For developers with 3-4 years of experience"

CHAPTER_FILES = [
    "01-core-java.md",
    "02-collections-and-streams.md",
    "03-concurrency-and-jvm.md",
    "04-spring.md",
    "05-sql-jpa-hibernate.md",
    "06-rest-and-microservices.md",
    "07-security.md",
    "08-testing-debugging-coding.md",
    "09-messaging-and-caching.md",
    "10-production-operations.md",
]

# (file, heading shown in the manuscript). The heading text of each extras file
# is replaced so the combined document has a predictable structure.
FRONT_MATTER = ["how-to-use-this-book.md"]
BACK_MATTER = ["top-40.md", "study-plan.md", "mini-exercises.md", "glossary.md",
               "coverage-checklist.md"]

INTRO = f"""# {TITLE}

*{SUBTITLE}*

**Stack assumed throughout:** Java 17 and 21, Spring Boot 3, REST over HTTP,
PostgreSQL with JPA and Hibernate, JUnit 5 with Mockito, Maven or Gradle, and a
production environment with Redis, Kafka, Docker and an observability stack.

Two hundred questions, numbered Q001 to Q200, each with a priority, a spoken
answer of roughly 45-90 seconds, a deeper explanation, a practical example,
follow-up questions, common mistakes, a production perspective and the related
concepts it opens up.

This book contains no interview-frequency statistics, no benchmark numbers and
no invented citations. Where a claim would require measurement in your own
system, the text says so.
"""


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip("\n")


def slug(text: str) -> str:
    """GitHub-style anchor slug, good enough for the chapter/section links used here."""
    lowered = text.strip().lower()
    lowered = re.sub(r"[^a-z0-9 \-]", "", lowered)
    return lowered.replace(" ", "-")


def demote_headings(text: str) -> str:
    """Extras files are standalone documents with an H1; nest them one level deeper."""
    return re.sub(r"^(#{1,5}) ", lambda m: "#" * (len(m.group(1)) + 1) + " ", text, flags=re.M)


def main() -> int:
    chapters = []
    for name in CHAPTER_FILES:
        path = ROOT / "chapters" / name
        if not path.exists():
            print(f"missing chapter source: {path}", file=sys.stderr)
            return 1
        text = read(path)
        heading = text.splitlines()[0].lstrip("# ").strip()
        chapters.append((heading, text))

    extras_front = []
    for name in FRONT_MATTER:
        path = ROOT / "extras" / name
        if not path.exists():
            print(f"missing extras source: {path}", file=sys.stderr)
            return 1
        text = read(path)
        heading = text.splitlines()[0].lstrip("# ").strip()
        extras_front.append((heading, demote_headings(text)))

    extras_back = []
    for name in BACK_MATTER:
        path = ROOT / "extras" / name
        if not path.exists():
            print(f"missing extras source: {path}", file=sys.stderr)
            return 1
        text = read(path)
        heading = text.splitlines()[0].lstrip("# ").strip()
        extras_back.append((heading, demote_headings(text)))

    toc = ["## Contents", ""]
    for heading, _ in extras_front:
        toc.append(f"- [{heading}](#{slug(heading)})")
    for heading, body in chapters:
        count = len(re.findall(r"^## Q\d{3}\.", body, re.M))
        ids = re.findall(r"^## (Q\d{3})\.", body, re.M)
        span = f"{ids[0]}-{ids[-1]}" if ids else ""
        toc.append(f"- [{heading}](#{slug(heading)}) — {count} questions ({span})")
    for heading, _ in extras_back:
        toc.append(f"- [{heading}](#{slug(heading)})")
    toc.append("")

    parts = [INTRO, "\n".join(toc)]
    for _, body in extras_front:
        parts.append(body)
    for _, body in chapters:
        parts.append(body)
    for _, body in extras_back:
        parts.append(body)

    combined = "\n\n---\n\n".join(part.strip("\n") for part in parts) + "\n"
    OUTPUT.write_text(combined, encoding="utf-8")

    questions = len(re.findall(r"^## Q\d{3}\.", combined, re.M))
    words = len(combined.split())
    print(f"wrote {OUTPUT.relative_to(ROOT.parent)}")
    print(f"  questions={questions} words={words} bytes={OUTPUT.stat().st_size}")
    return 0 if questions == 200 else 1


if __name__ == "__main__":
    raise SystemExit(main())
