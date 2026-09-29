# Java Backend Interview Book

This workspace currently contains a **200-question master plan** and a fully written **Chapter 1 (Q001-Q030)**. The remaining nine chapters, combined manuscript and final PDF are **not yet complete**. Do not mistake the plan for 200 finished answers.

## Files

- `question-plan.md`: selection plan with 200 IDs, priorities, concepts, follow-ups and rationale.
- `chapters/01-core-java.md`: complete first chapter with all required answer sections.
- `extras/`: top 40, seven-day plan, mini-exercises with outlines and glossary. References beyond Q030 point to planned questions, not completed answers.
- `scripts/validate.mjs`: checks plan order, duplicate titles, completed chapter counts, required sections and extra references.
- `scripts/build.mjs`: assembles Markdown and uses `pdf-lib` to typeset a PDF with title page, contents page and page numbers. It refuses incomplete manuscripts.
- `PROGRESS.md`: continuation checkpoint.

## Commands

From the project root:

```sh
node java-backend-interview-book/scripts/validate.mjs --allow-partial
node java-backend-interview-book/scripts/validate.mjs
node java-backend-interview-book/scripts/build.mjs
```

The second and third commands intentionally fail until all chapters exist. Once complete, the exact rebuild command is `node java-backend-interview-book/scripts/build.mjs`. It writes `Java_Backend_Top_200_Interview_Questions.md` and `Java_Backend_Top_200_Interview_Questions.pdf` beside this README. `pdf-lib` is installed as a project dependency. The PDF script does not yet implement clickable TOC links and uses built-in fonts with ASCII-safe punctuation. A final PDF must be opened or text-extracted and checked for Q001 and Q200 before it can be called verified.

The adjacent Vite application is a searchable reader for the master plan and completed answer chapter, not a substitute for the unfinished PDF.