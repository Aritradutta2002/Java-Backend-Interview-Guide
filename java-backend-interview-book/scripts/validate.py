#!/usr/bin/env python3
"""Structural validation for the Top 200 Java Backend Interview book.

Pure standard library. Run from anywhere:

    python3 java-backend-interview-book/scripts/validate.py
    python3 java-backend-interview-book/scripts/validate.py --allow-partial

Checks performed
  1. question-plan.md contains exactly 200 rows, Q001..Q200 in order, with the
     requested per-chapter counts and no duplicate titles.
  2. Each chapter file holds its expected number of main questions, numbered
     continuously, matching the plan titles.
  3. Every main question carries all nine required labelled answer sections and
     at least two "Common follow-ups" bullets.
  4. Every Qxxx reference in the extras (top 40, study plan, mini exercises,
     glossary) resolves to a real question ID, and the Top 40 file lists
     exactly 40 distinct IDs.
  5. No placeholder text and no unbalanced code fences remain anywhere.
  6. When the combined manuscript exists it is checked the same way.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CHAPTERS: list[tuple[str, str, int]] = [
    ("01-core-java.md", "Core Java, OOP, exceptions, and language fundamentals", 30),
    ("02-collections-and-streams.md", "Collections, generics, streams, and functional Java", 20),
    ("03-concurrency-and-jvm.md", "Concurrency, asynchronous programming, and JVM", 25),
    ("04-spring.md", "Spring Framework and Spring Boot", 30),
    ("05-sql-jpa-hibernate.md", "SQL, transactions, JPA, and Hibernate", 30),
    ("06-rest-and-microservices.md", "HTTP, REST APIs, and microservices", 25),
    ("07-security.md", "Security", 12),
    ("08-testing-debugging-coding.md", "Testing, debugging, and coding exercises", 13),
    ("09-messaging-and-caching.md", "Messaging and caching", 10),
    ("10-production-operations.md", "Deployment, observability, and production troubleshooting", 5),
]

REQUIRED_SECTIONS = [
    "Priority:",
    "Why interviewers ask it:",
    "Interview-ready answer:",
    "In-depth explanation:",
    "Practical backend example:",
    "Common follow-ups:",
    "Mistakes to avoid:",
    "Production perspective:",
    "Related concepts covered:",
]

PRIORITIES = {"Must Know", "Important", "Bonus"}

PLACEHOLDER_PATTERNS = [
    r"\bTODO\b",
    r"\bTBD\b",
    r"\bFIXME\b",
    r"\bXXX\b",
    r"\blorem ipsum\b",
    r"\bcoming soon\b",
    r"\bto be written\b",
    r"\bplaceholder\b",
    r"\[\s*\]\(\s*\)",
    r"<\s*insert[^>]*>",
]

QID = re.compile(r"\bQ(\d{3})\b")
HEADING = re.compile(r"^## (Q\d{3})\.\s+(.+?)\s*$", re.M)
PLAN_ROW = re.compile(r"^\|\s*(Q\d{3})\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|", re.M)
PLAN_SECTION = re.compile(r"^##\s+(\d+)\.\s+(.*)$", re.M)


def qid(n: int) -> str:
    return f"Q{n:03d}"


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.checks: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def ok(self, msg: str) -> None:
        self.checks.append(msg)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def strip_code(text: str) -> str:
    """Remove fenced code blocks so prose checks ignore code samples."""
    return re.sub(r"```.*?```", "", text, flags=re.S)


def check_placeholders(rep: Report, label: str, text: str) -> None:
    prose = strip_code(text)
    for pattern in PLACEHOLDER_PATTERNS:
        for match in re.finditer(pattern, prose, flags=re.I):
            line = prose[: match.start()].count("\n") + 1
            rep.error(f"{label}: placeholder text {match.group(0)!r} near line {line}.")


def check_fences(rep: Report, label: str, text: str) -> None:
    fences = re.findall(r"^```", text, flags=re.M)
    if len(fences) % 2 != 0:
        rep.error(f"{label}: unbalanced code fences ({len(fences)} fence markers).")


def validate_plan(rep: Report) -> dict[str, str]:
    path = ROOT / "question-plan.md"
    if not path.exists():
        rep.error("question-plan.md is missing.")
        return {}
    text = read(path)
    check_placeholders(rep, "question-plan.md", text)
    check_fences(rep, "question-plan.md", text)

    rows = PLAN_ROW.findall(text)
    ids = [r[0] for r in rows]
    titles = {r[0]: r[1] for r in rows}

    if len(ids) != 200:
        rep.error(f"question-plan.md has {len(ids)} question rows, expected 200.")
    for index, value in enumerate(ids, start=1):
        if value != qid(index):
            rep.error(f"question-plan.md row {index} is {value}, expected {qid(index)}.")
            break
    else:
        if len(ids) == 200:
            rep.ok("Plan lists Q001-Q200 exactly once, in order.")

    lowered = [t.strip().lower() for t in titles.values()]
    duplicates = {t for t in lowered if lowered.count(t) > 1}
    if duplicates:
        rep.error(f"question-plan.md has duplicate question titles: {sorted(duplicates)[:3]}")
    else:
        rep.ok("Plan has no duplicate main-question titles.")

    for _, _, priority in rows:
        if priority.strip() not in PRIORITIES:
            rep.error(f"question-plan.md has unknown priority {priority!r}.")
            break
    else:
        rep.ok("Plan priorities all use Must Know / Important / Bonus.")

    # Per-chapter counts inside the plan.
    boundaries = [(m.start(), int(m.group(1))) for m in PLAN_SECTION.finditer(text)]
    for position, (start, number) in enumerate(boundaries):
        end = boundaries[position + 1][0] if position + 1 < len(boundaries) else len(text)
        if number < 1 or number > len(CHAPTERS):
            continue
        count = len(PLAN_ROW.findall(text[start:end]))
        expected = CHAPTERS[number - 1][2]
        if count != expected:
            rep.error(f"question-plan.md chapter {number} lists {count} questions, expected {expected}.")
    if not rep.errors:
        rep.ok("Plan per-chapter counts match the requested distribution.")
    return titles


def split_questions(text: str) -> list[tuple[str, str, str]]:
    """Return (id, title, body) for every '## Qxxx.' heading."""
    matches = list(HEADING.finditer(text))
    out = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        out.append((match.group(1), match.group(2), text[start:end]))
    return out


def validate_question(rep: Report, label: str, question_id: str, title: str, body: str) -> None:
    for section in REQUIRED_SECTIONS:
        if f"**{section}" not in body:
            rep.error(f"{label} {question_id}: missing section '{section.rstrip(':')}'.")
    priority_match = re.search(r"\*\*Priority:\*\*\s*([A-Za-z ]+)", body)
    if priority_match and priority_match.group(1).strip() not in PRIORITIES:
        rep.error(f"{label} {question_id}: priority {priority_match.group(1).strip()!r} is not valid.")
    follow = re.search(r"\*\*Common follow-ups:\*\*(.*?)(?=\*\*Mistakes to avoid|\Z)", body, re.S)
    if follow:
        bullets = [line for line in follow.group(1).splitlines() if line.strip().startswith("- ")]
        if len(bullets) < 2:
            rep.error(f"{label} {question_id}: needs at least 2 follow-up bullets, found {len(bullets)}.")
        if len(bullets) > 4:
            rep.warn(f"{label} {question_id}: has {len(bullets)} follow-ups (spec suggests 2-4).")
    if not title.endswith(("?", ".")):
        rep.warn(f"{label} {question_id}: title does not read as a question or instruction.")
    words = len(strip_code(body).split())
    if words < 150:
        rep.error(f"{label} {question_id}: answer is only {words} words, likely truncated.")


def validate_chapters(rep: Report, plan_titles: dict[str, str], allow_partial: bool) -> list[str]:
    expected_next = 1
    seen: list[str] = []
    all_titles: dict[str, str] = {}
    for filename, chapter_title, expected_count in CHAPTERS:
        path = ROOT / "chapters" / filename
        if not path.exists():
            if not allow_partial:
                rep.error(f"Missing chapter file chapters/{filename}.")
            expected_next += expected_count
            continue
        text = read(path)
        check_placeholders(rep, f"chapters/{filename}", text)
        check_fences(rep, f"chapters/{filename}", text)
        questions = split_questions(text)
        if len(questions) != expected_count:
            rep.error(
                f"chapters/{filename} has {len(questions)} main questions, expected {expected_count}."
            )
        for question_id, title, body in questions:
            if question_id != qid(expected_next):
                rep.error(
                    f"chapters/{filename}: found {question_id} where {qid(expected_next)} was expected."
                )
            expected_next += 1
            seen.append(question_id)
            validate_question(rep, f"chapters/{filename}", question_id, title, body)
            key = title.strip().lower()
            if key in all_titles:
                rep.error(f"Duplicate main question title: {question_id} repeats {all_titles[key]}.")
            else:
                all_titles[key] = question_id
            planned = plan_titles.get(question_id)
            if planned and planned.strip().lower() != key:
                rep.warn(
                    f"{question_id} title differs from the plan.\n"
                    f"      plan: {planned.strip()}\n      book: {title.strip()}"
                )
        if len(questions) == expected_count:
            rep.ok(f"chapters/{filename}: {expected_count} questions, sections complete.")
    if not allow_partial:
        if len(seen) != 200:
            rep.error(f"Found {len(seen)} main questions across chapters, expected 200.")
        else:
            rep.ok("Exactly 200 main question IDs across all chapters (Q001-Q200, each once).")
    return seen


def validate_extras(rep: Report, known: set[str], allow_partial: bool) -> None:
    extras_dir = ROOT / "extras"
    for path in sorted(extras_dir.glob("*.md")):
        text = read(path)
        label = f"extras/{path.name}"
        check_placeholders(rep, label, text)
        check_fences(rep, label, text)
        referenced = {f"Q{m.group(1)}" for m in QID.finditer(text)}
        unknown = sorted(r for r in referenced if not (1 <= int(r[1:]) <= 200))
        if unknown:
            rep.error(f"{label} references non-existent question IDs: {unknown}")
        if not allow_partial:
            missing = sorted(r for r in referenced if r not in known)
            if missing:
                rep.error(f"{label} references IDs absent from the chapters: {missing}")
        if path.name == "top-40.md":
            ids = [m.group(0) for m in QID.finditer(text)]
            table_ids = re.findall(r"^\|\s*(Q\d{3})\s*\|", text, re.M)
            unique = sorted(set(table_ids))
            if len(unique) != 40:
                rep.error(f"{label} lists {len(unique)} distinct question IDs in its table, expected 40.")
            elif len(table_ids) != 40:
                rep.error(f"{label} has {len(table_ids)} table rows, expected 40 unique rows.")
            else:
                rep.ok("Top 40 references 40 distinct, real question IDs.")
            del ids
        if path.name == "study-plan.md" and not allow_partial:
            days = re.findall(r"^##\s+Day\s+(\d)", text, re.M)
            if sorted(days) != [str(d) for d in range(1, 8)]:
                rep.error(f"{label} must contain Day 1 through Day 7 headings, found {days}.")
            else:
                rep.ok("Study plan covers Day 1 to Day 7 with concrete question IDs.")


def validate_combined(rep: Report, allow_partial: bool) -> None:
    path = ROOT / "Java_Backend_Top_200_Interview_Questions.md"
    if not path.exists():
        if not allow_partial:
            rep.error("Combined manuscript Java_Backend_Top_200_Interview_Questions.md is missing.")
        return
    text = read(path)
    check_placeholders(rep, path.name, text)
    check_fences(rep, path.name, text)
    ids = [m.group(1) for m in HEADING.finditer(text)]
    if ids != [qid(n) for n in range(1, 201)]:
        rep.error(
            f"{path.name}: main question headings are not exactly Q001..Q200 in order (found {len(ids)})."
        )
    else:
        rep.ok("Combined manuscript contains Q001-Q200 in order.")
    for needed in ("Top 40 Questions to Revise First", "How to Use This Book",
                   "7-Day Interview Preparation Plan", "Practical Mini-Exercises",
                   "Glossary", "Final Coverage Checklist"):
        if needed not in text:
            rep.error(f"{path.name}: required section '{needed}' is missing.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the interview book sources.")
    parser.add_argument("--allow-partial", action="store_true",
                        help="Permit chapters/extras that are not written yet.")
    args = parser.parse_args()

    rep = Report()
    plan_titles = validate_plan(rep)
    seen = validate_chapters(rep, plan_titles, args.allow_partial)
    validate_extras(rep, set(seen), args.allow_partial)
    validate_combined(rep, args.allow_partial)

    print("=" * 72)
    print("Java Backend Interview Book - source validation")
    print("=" * 72)
    for line in rep.checks:
        print(f"  PASS  {line}")
    for line in rep.warnings:
        print(f"  WARN  {line}")
    for line in rep.errors:
        print(f"  FAIL  {line}")
    print("-" * 72)
    mode = "partial" if args.allow_partial else "full"
    print(f"mode={mode}  questions_written={len(seen)}  warnings={len(rep.warnings)}  errors={len(rep.errors)}")
    if rep.errors:
        print("RESULT: FAILED")
        return 1
    print("RESULT: PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
