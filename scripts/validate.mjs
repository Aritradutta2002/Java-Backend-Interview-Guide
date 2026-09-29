import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const counts = [30, 20, 25, 30, 30, 25, 12, 13, 10, 5];
const files = [
  '01-core-java.md', '02-collections-and-streams.md', '03-concurrency-and-jvm.md',
  '04-spring.md', '05-sql-jpa-hibernate.md', '06-rest-and-microservices.md',
  '07-security.md', '08-testing-debugging-coding.md', '09-messaging-and-caching.md',
  '10-production-operations.md',
];
const required = [
  'Priority', 'Why interviewers ask it', 'Interview-ready answer', 'In-depth explanation',
  'Practical backend example', 'Common follow-ups', 'Mistakes to avoid',
  'Production perspective', 'Related concepts covered',
];
const id = n => `Q${String(n).padStart(3, '0')}`;
const errors = [];
const plan = fs.readFileSync(path.join(root, 'question-plan.md'), 'utf8');
const planned = [...plan.matchAll(/^\| (Q\d{3}) \|/gm)].map(m => m[1]);
if (planned.length !== 200 || new Set(planned).size !== 200) errors.push(`Plan has ${planned.length} rows / ${new Set(planned).size} unique IDs, expected 200.`);
for (let n = 1; n <= 200; n++) if (planned[n - 1] !== id(n)) errors.push(`Plan position ${n} must be ${id(n)}.`);
for (let i = 0; i < counts.length; i++) {
  const section = plan.match(new RegExp(`^## ${i + 1}\\.[^\\n]*\\n([\\s\\S]*?)(?=^## (?:${i + 2}\\.|Selection review)|$(?![\\s\\S]))`, 'm'))?.[1] || '';
  const count = [...section.matchAll(/^\| Q\d{3} \|/gm)].length;
  if (count !== counts[i]) errors.push(`Plan chapter ${i + 1} has ${count} rows, expected ${counts[i]}.`);
}
const titles = [...plan.matchAll(/^\| Q\d{3} \| ([^|]+) \|/gm)].map(m => m[1].trim().toLowerCase());
if (new Set(titles).size !== titles.length) errors.push('Duplicate main-question title in plan.');

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
  const sections = [...text.matchAll(/^## (Q\d{3})\. ([^\n]+)\n([\s\S]*?)(?=^## Q\d{3}\. |$(?![\s\S]))/gm)];
  if (sections.length !== expected) errors.push(`${files[chapter]} has ${sections.length} questions, expected ${expected}.`);
  for (let j = 0; j < sections.length; j++) {
    const [, actual, title, body] = sections[j];
    if (actual !== id(next + j)) errors.push(`${files[chapter]} question ${j + 1} is ${actual}, expected ${id(next + j)}.`);
    if (!titles.includes(title.trim().toLowerCase())) errors.push(`${actual} title differs from plan.`);
    for (const label of required) {
      const pattern = new RegExp(`\\*\\*${label}:\\*\\*|\\*\\*${label}\\*\\*:`);
      if (!pattern.test(body)) errors.push(`${actual} lacks ${label}.`);
    }
    if ((body.match(/^- /gm) || []).length < 2) errors.push(`${actual} lacks two follow-ups.`);
    if (/\b(TODO|TBD|PLACEHOLDER|Lorem ipsum)\b/i.test(body)) errors.push(`${actual} contains placeholder text.`);
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
  for (const ref of fs.readFileSync(file, 'utf8').match(/Q\d{3}/g) || []) {
    if (!planned.includes(ref)) errors.push(`${extra} references missing ${ref}.`);
  }
  if (extra === 'extras/top-40.md') {
    const top = [...fs.readFileSync(file, 'utf8').matchAll(/^\| (Q\d{3}) \|/gm)].map(m => m[1]);
    if (top.length !== 40 || new Set(top).size !== 40) errors.push(`Top 40 has ${top.length} rows / ${new Set(top).size} unique IDs, expected 40.`);
  }
}
if (errors.length) {
  console.error(errors.join('\n'));
  process.exitCode = 1;
} else {
  console.log(`PASS: ${planned.length} unique planned IDs, ${completed} completed answers, chapter structure and references valid.${completed === 200 ? ' Book complete.' : ' Partial manuscript.'}`);
}