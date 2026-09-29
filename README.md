# Java Backend Interview Guide

This repository contains **[Top 200 Java Backend Developer Interview Questions and Answers](java-backend-interview-book/)** — a complete interview-preparation book for developers with roughly 3–4 years of Java experience.

- 📕 **Read the PDF:** [`java-backend-interview-book/Java_Backend_Top_200_Interview_Questions.pdf`](java-backend-interview-book/Java_Backend_Top_200_Interview_Questions.pdf) (214 pages, clickable contents, bookmarks, page numbers)
- 📝 **Read in Markdown:** [`java-backend-interview-book/Java_Backend_Top_200_Interview_Questions.md`](java-backend-interview-book/Java_Backend_Top_200_Interview_Questions.md), or chapter by chapter under [`java-backend-interview-book/chapters/`](java-backend-interview-book/chapters)
- 🛠 **Build, validate and edit:** see [`java-backend-interview-book/README.md`](java-backend-interview-book/README.md)

## What is inside

200 questions numbered Q001–Q200 across ten chapters — core Java, collections and streams, concurrency and the JVM, Spring Boot, SQL and Hibernate, REST and microservices, security, testing and debugging, messaging and caching, and production operations. Each question has a priority, a spoken answer of roughly 45–90 seconds, an in-depth explanation, a practical backend example, follow-up questions with answers, common mistakes, a production perspective and related concepts.

Extras: a Top 40 to revise first, a guide to using the book, a 7-day study plan, twelve practical mini-exercises tied to question IDs, a glossary and a final coverage checklist.

**Stack assumed:** Java 17 and 21, Spring Boot 3, PostgreSQL, JPA and Hibernate, JUnit 5 with Mockito, Maven or Gradle, Redis, Kafka, Docker and observability tooling.

## Rebuild in one command

```bash
python3 -m venv .venv && .venv/bin/pip install reportlab pypdf
python3 java-backend-interview-book/scripts/validate.py && \
python3 java-backend-interview-book/scripts/build_book.py && \
.venv/bin/python java-backend-interview-book/scripts/build_pdf.py && \
.venv/bin/python java-backend-interview-book/scripts/verify_pdf.py
```
