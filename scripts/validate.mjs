import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const counts = [30, 20, 25, 30, 30, 25, 12, 13, 10, 5];
const files = [
  '01-core-java.md',
  '02-collections-generics-streams.md',
  '03-concurrency-async-jvm.md',
  '04-spring-framework-boot.md',
  '05-sql-jpa-hibernate.md',
  '06-http-rest-microservices.md',
  '07-security.md',
  '08-testing-debugging.md',
  '09-messaging-caching.md',
  '10-deployment-observability.md',
];

const id = n => `Q${String(n).padStart(3, '0')}`;
const errors = [];
// The README advertises a fixed answer format. Without enforcement, chapters drift:
// as of the audit only Chapter 1 delivered it for all 30 questions.
const strictTemplate = process.argv.includes('--strict-template');
const templateGaps = [];
const templateSections = [
  [/^\*\*The one-line answer:\*\*/m, 'one-line answer'],
  [/^### Common follow-up/m, 'common follow-ups'],
  [/^### Mistakes to avoid/m, 'mistakes to avoid'],
  [/^### Production perspective/m, 'production perspective'],
  [/```/, 'code example'],
];

const plan = fs.readFileSync(path.join(root, 'Questions.md'), 'utf8');
const plannedMatches = [...plan.matchAll(/^- (Q\d{3}) \| ([^|]+) \| ([^|]+) \|/gm)];
const planned = plannedMatches.map(m => m[1]);
const planTitles = Object.fromEntries(plannedMatches.map(m => [m[1], m[2].trim()]));

if (planned.length !== 200 || new Set(planned).size !== 200) {
  errors.push(`Plan has ${planned.length} rows / ${new Set(planned).size} unique IDs, expected 200.`);
}

for (let n = 1; n <= 200; n++) {
  if (planned[n - 1] !== id(n)) errors.push(`Plan position ${n} must be ${id(n)}, found ${planned[n - 1]}.`);
}

let next = 1;
let completed = 0;

for (let chapter = 0; chapter < files.length; chapter++) {
  const file = path.join(root, 'chapters', files[chapter]);
  const expected = counts[chapter];
  if (!fs.existsSync(file)) {
    if (!process.argv.includes('--allow-partial')) errors.push(`Missing chapter ${files[chapter]}.`);
    next += expected;
    continue;
  }

  const text = fs.readFileSync(file, 'utf8');
  const sections = [...text.matchAll(/^## (Q\d{3})[.—:\s]+([^\n]+)\n([\s\S]*?)(?=^## Q\d{3}[.—:\s]+|$(?![\s\S]))/gm)];

  if (sections.length !== expected) {
    errors.push(`${files[chapter]} has ${sections.length} questions, expected ${expected}.`);
  }

  for (let j = 0; j < sections.length; j++) {
    const [, actual, title, body] = sections[j];
    const expectedId = id(next + j);

    if (actual !== expectedId) {
      errors.push(`${files[chapter]} question ${j + 1} is ${actual}, expected ${expectedId}.`);
    }

    if (body.trim().length < 100) {
      errors.push(`${actual} has insufficient content (${body.trim().length} chars).`);
    }

    if (/\b(TODO|TBD|PLACEHOLDER|Lorem ipsum)\b/i.test(body)) {
      errors.push(`${actual} contains placeholder text.`);
    }

    const missing = templateSections.filter(([re]) => !re.test(body)).map(([, label]) => label);
    if (missing.length) {
      templateGaps.push(`${actual} (${files[chapter]}): missing ${missing.join(', ')}`);
    }
  }

  completed += sections.length;
  next += expected;
}

for (const extra of ['extras/top-40.md', 'extras/study-plan.md']) {
  const file = path.join(root, extra);
  if (!fs.existsSync(file)) {
    if (!process.argv.includes('--allow-partial')) errors.push(`Missing ${extra}.`);
    continue;
  }
  const refs = fs.readFileSync(file, 'utf8').match(/Q\d{3}/g) || [];
  for (const ref of refs) {
    if (!planned.includes(ref)) errors.push(`${extra} references missing question ID ${ref}.`);
  }
}

if (templateGaps.length) {
  const summary = `${templateGaps.length} of ${completed} questions are missing template sections:\n  ${templateGaps.join('\n  ')}`;
  if (strictTemplate) errors.push(summary);
  else console.warn(`WARN - ${summary}`);
}

if (errors.length) {
  console.error('Validation failed:');
  console.error(errors.join('\n'));
  process.exitCode = 1;
} else if (templateGaps.length === 0) {
  console.log(`PASS: ${planned.length} unique planned IDs in Questions.md, ${completed} completed answers across 10 chapters. All questions valid and interview-ready.`);
} else {
  console.log(`PASS (with warnings): ${planned.length} unique planned IDs, ${completed} answers, ${templateGaps.length} template gaps. Run with --strict-template to fail on them.`);
}