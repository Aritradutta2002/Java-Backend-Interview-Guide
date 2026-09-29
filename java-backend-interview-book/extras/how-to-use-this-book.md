# How to Use This Book

This book contains 200 interview questions with complete answers, aimed at a backend developer with roughly three to four years of Java experience. It assumes Java 17 or 21, Spring Boot 3, PostgreSQL with JPA and Hibernate, JUnit 5 with Mockito, Maven or Gradle, and the usual production surroundings of Redis, Kafka, Docker and an observability stack.

## What each question contains

Every question follows the same nine-part structure, so you can navigate by section rather than reading linearly.

| Section | What it is for |
|---|---|
| **Priority** | Must Know, Important or Bonus — used to triage when time is short. |
| **Why interviewers ask it** | The signal the question is probing, in one sentence. |
| **Interview-ready answer** | A spoken answer of roughly 45–90 seconds. This is the part to rehearse aloud. |
| **In-depth explanation** | The understanding behind the spoken answer, for follow-up questions and for real work. |
| **Practical backend example** | A compact, correct snippet in Java, SQL, YAML or a short checklist. |
| **Common follow-ups** | The questions that usually come next, with brief answers. |
| **Mistakes to avoid** | Answers and implementations that cost candidates offers or cause incidents. |
| **Production perspective** | What the topic looks like when a real system depends on it. |
| **Related concepts covered** | Threads to pull if you want to go deeper. |

## A study method that works

1. **Read the question, then answer it out loud before reading on.** Recall is what builds fluency; rereading builds only familiarity.
2. **Time yourself against 45–90 seconds.** Interview answers that run past two minutes without a pause lose the room, and answers under twenty seconds sound thin.
3. **Compare with the interview-ready answer and note only the gaps.** Do not memorise the wording — the phrasing should be yours.
4. **Answer the follow-ups without looking.** Interviewers rarely stop at the first question; the follow-up is usually where the decision is made.
5. **Run the example.** Type the snippet into a scratch project or a SQL console. Reading code and writing code produce very different levels of retention.
6. **Mark a question done only when you can state one trade-off and one production implication in your own words.** That is the standard the answers were written to.

## Triage when you have limited time

- **Two evenings:** the 40 questions in `top-40.md`, spoken aloud.
- **One week:** the 7-day plan in `study-plan.md`, which assigns all 200 questions across seven sessions.
- **Longer runway:** read chapter by chapter and do the exercises in `mini-exercises.md`, which are tied to specific question IDs.

If you are interviewing for a specific role, reweight accordingly: a data-heavy role puts Chapter 5 first, a platform role puts Chapters 3, 9 and 10 first, and a product-team role puts Chapters 4, 6 and 8 first.

## How to answer well in the room

- **Start with the direct answer, then justify it.** Do not narrate your way to the point.
- **Name your assumptions.** "Assuming PostgreSQL and a single service" is a strong opening, not a hedge.
- **Prefer "it depends, and here is what it depends on".** Then pick a default and defend it — an unresolved "it depends" reads as evasion.
- **Say when you do not know.** Then describe how you would find out. That answer beats a confident invention every time.
- **Use concrete examples from your own work.** The answers here give you structure; your experience gives them credibility.

## What this book deliberately does not do

- It contains no interview-frequency statistics, no benchmark numbers and no citations to studies. Nothing here is invented to sound authoritative, so where a claim would need measurement, the text tells you to measure instead.
- It avoids trivia that has no bearing on real work.
- It does not present version-dependent behaviour as universal. Where something changed between Java or Spring Boot versions, the version is stated.
- It does not tell you that one technology is always better than another. Where a choice exists, the text explains when each option is the right one.
