# Top 200 Java Backend Developer Interview Questions and Answers

A complete, self-contained interview-preparation book for backend developers with roughly **3–4 years of Java experience**, delivered as a readable PDF plus editable Markdown sources and a reproducible build.

**Stack assumed throughout:** Java 17 and 21, Spring Boot 3 (Spring Framework 6, Spring Security 6), REST over HTTP, PostgreSQL with JPA and Hibernate 6, JUnit 5 with Mockito and Testcontainers, Maven or Gradle, and a production environment with Redis, Kafka, Docker and an observability stack.

## Deliverables

| File | What it is |
|---|---|
| [`Java_Backend_Top_200_Interview_Questions.pdf`](Java_Backend_Top_200_Interview_Questions.pdf) | The book: 214 pages, title page, clickable contents, PDF bookmarks, page numbers. |
| [`Java_Backend_Top_200_Interview_Questions.md`](Java_Backend_Top_200_Interview_Questions.md) | The same content as one Markdown file (generated — do not edit by hand). |
| [`chapters/`](chapters) | Ten chapter sources, one file per chapter. **Edit these.** |
| [`extras/`](extras) | Top 40, how to use the book, 7-day plan, mini-exercises, glossary, coverage checklist. |
| [`question-plan.md`](question-plan.md) | The master plan: 200 rows with ID, title, priority, concepts, likely follow-up and rationale. |
| [`scripts/`](scripts) | Validation and build scripts (`validate.py`, `build_book.py`, `build_pdf.py`, `verify_pdf.py`). |

## Contents at a glance

| # | Chapter | Questions | IDs |
|---|---|---|---|
| 1 | Core Java, OOP, exceptions, language fundamentals | 30 | Q001–Q030 |
| 2 | Collections, generics, streams, functional Java | 20 | Q031–Q050 |
| 3 | Concurrency, asynchronous programming, JVM | 25 | Q051–Q075 |
| 4 | Spring Framework and Spring Boot | 30 | Q076–Q105 |
| 5 | SQL, transactions, JPA, Hibernate | 30 | Q106–Q135 |
| 6 | HTTP, REST APIs, microservices | 25 | Q136–Q160 |
| 7 | Security | 12 | Q161–Q172 |
| 8 | Testing, debugging, coding exercises | 13 | Q173–Q185 |
| 9 | Messaging and caching | 10 | Q186–Q195 |
| 10 | Deployment, observability, production troubleshooting | 5 | Q196–Q200 |
| | **Total** | **200** | **Q001–Q200** |

Every question contains all ten required elements: the question as an interviewer would ask it, a **Priority** (Must Know / Important / Bonus), **Why interviewers ask it**, an **Interview-ready answer** of roughly 45–90 spoken seconds, an **In-depth explanation**, a **Practical backend example**, 2–4 **Common follow-ups** with brief answers, **Mistakes to avoid**, a **Production perspective**, and **Related concepts covered**.

## Rebuilding the book

The build is Python-only and needs two packages. From the **repository root**:

```bash
# one-time bootstrap
python3 -m venv .venv
.venv/bin/pip install reportlab pypdf

# rebuild everything (combined Markdown -> PDF), then verify
python3 java-backend-interview-book/scripts/validate.py
python3 java-backend-interview-book/scripts/build_book.py
.venv/bin/python java-backend-interview-book/scripts/build_pdf.py
.venv/bin/python java-backend-interview-book/scripts/verify_pdf.py
```

One-liner for a full rebuild after editing a chapter:

```bash
python3 java-backend-interview-book/scripts/validate.py && \
python3 java-backend-interview-book/scripts/build_book.py && \
.venv/bin/python java-backend-interview-book/scripts/build_pdf.py && \
.venv/bin/python java-backend-interview-book/scripts/verify_pdf.py
```

`validate.py` and `build_book.py` use only the Python standard library; `build_pdf.py` needs **reportlab** and `verify_pdf.py` needs **pypdf**.

### Why ReportLab rather than Pandoc

Pandoc, LaTeX, wkhtmltopdf and WeasyPrint were all unavailable in the environment this book was produced in, so the PDF is rendered by a self-contained ReportLab pipeline in `scripts/build_pdf.py`. It parses the Markdown subset the manuscript uses (ATX headings, paragraphs, bullet and numbered lists, fenced code blocks, pipe tables, bold, italic, inline code, links) and produces:

- a title page and a generated table of contents with dot leaders, page numbers and **clickable internal links**;
- **PDF outline bookmarks** for every chapter, extras section and question;
- running headers and `Page N of M` footers (the build runs two passes so the total is correct);
- code blocks in a boxed monospace style with long lines wrapped rather than clipped;
- tables with repeating header rows.

If you have Pandoc available and prefer it, the combined Markdown is a normal document and `pandoc Java_Backend_Top_200_Interview_Questions.md -o book.pdf --toc` will work, but that path has not been exercised here and the styling will differ.

## Validation

```bash
python3 java-backend-interview-book/scripts/validate.py            # full check, exits non-zero on failure
python3 java-backend-interview-book/scripts/validate.py --allow-partial   # while chapters are in progress
```

`validate.py` checks:

- the master plan holds Q001–Q200 exactly once, in order, with valid priorities and the required per-chapter counts;
- each chapter file contains its expected number of main questions, numbered continuously and titled exactly as in the plan;
- every question carries all nine labelled sections, at least two follow-up bullets (warning above four) and an interview-ready answer of reasonable length;
- exactly 200 unique main question IDs across the whole book, with no duplicate titles;
- every `Qxxx` reference in the extras resolves to a real question, the Top 40 table has 40 distinct rows, and the study plan covers Day 1 to Day 7;
- no draft or stub markers and no unbalanced code fences anywhere;
- the combined manuscript has Q001–Q200 in order plus all required extras sections.

`verify_pdf.py` independently re-opens the built PDF with pypdf and checks that it exists, is non-trivially sized, parses, has more than 100 pages, exposes all 200 question IDs and all ten chapter headings through text extraction, and contains outline bookmarks and link annotations.

Current status of both, on the committed sources:

```text
validate.py   mode=full  questions_written=200  warnings=0  errors=0   RESULT: PASSED
verify_pdf.py checks=20  failures=0                                    RESULT: PASSED
              214 pages, 936,589 bytes, 258 bookmarks, 434 link annotations
```

## Editing

1. Edit a file under `chapters/` or `extras/` — those are the only sources of truth.
2. Keep the question format: `## Qnnn. <question text>` followed by the nine `**Label:**` sections in order.
3. If you change a question title, change it in `question-plan.md` too — the validator compares them.
4. Re-run the rebuild one-liner above. Never edit `Java_Backend_Top_200_Interview_Questions.md`; it is regenerated from the sources.

## Conventions and honesty notes

- No interview-frequency statistics, benchmark numbers or invented citations appear anywhere. Where a claim would require measurement in your own system, the text says to measure.
- Version-dependent behaviour is attributed to its Java or Spring Boot version instead of being stated as universal.
- Where a question involves a choice, the answer explains when each option is appropriate rather than declaring a winner.
- Code and SQL were written for the stack above and reviewed for correctness, but the snippets are illustrative fragments, not a compiled project — adapt names and error handling to your codebase.
