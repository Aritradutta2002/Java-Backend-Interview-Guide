import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { PDFDocument, StandardFonts, rgb } from 'pdf-lib';
import './validate.mjs';

if (process.exitCode) throw new Error('Validation failed; PDF not built.');
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const chapterNames = [
  '01-core-java', '02-collections-and-streams', '03-concurrency-and-jvm', '04-spring',
  '05-sql-jpa-hibernate', '06-rest-and-microservices', '07-security',
  '08-testing-debugging-coding', '09-messaging-and-caching', '10-production-operations',
];
const extraNames = ['top-40', 'study-plan', 'mini-exercises', 'glossary'];
const read = name => fs.readFileSync(path.join(root, name), 'utf8');
const chapters = chapterNames.map(name => read(`chapters/${name}.md`));
const extras = extraNames.map(name => read(`extras/${name}.md`));
const title = 'Top 200 Java Backend Developer Interview Questions and Answers\n3-4 Years Experience';
const combined = `# ${title.replace('\n', ' - ')}\n\n## Contents\n\n${chapterNames.map((name, i) => `- [Chapter ${i + 1}](#chapter-${i + 1})`).join('\n')}\n${extraNames.map(name => `- [${name}](#${name})`).join('\n')}\n\n${chapters.join('\n\n')}\n\n${extras.join('\n\n')}`;
fs.writeFileSync(path.join(root, 'Java_Backend_Top_200_Interview_Questions.md'), combined);

const pdf = await PDFDocument.create();
pdf.setTitle(title.replace('\n', ' - '));
const regular = await pdf.embedFont(StandardFonts.Helvetica);
const bold = await pdf.embedFont(StandardFonts.HelveticaBold);
const mono = await pdf.embedFont(StandardFonts.Courier);
const ink = rgb(.12, .16, .19);
const muted = rgb(.38, .43, .46);
const accent = rgb(.67, .31, .14);
const size = [595.28, 841.89];
let page;
let y;
function newPage() { page = pdf.addPage(size); y = 786; }
function line(text, font = regular, fontSize = 10, color = ink, gap = 16) {
  if (y < 62) newPage();
  page.drawText(text, { x: 56, y, font, size: fontSize, color });
  y -= gap;
}
function wrap(text, font, fontSize, max = 482) {
  const words = text.split(/\s+/);
  const lines = [];
  let current = '';
  for (const word of words) {
    if (!word) continue;
    const candidate = current ? `${current} ${word}` : word;
    if (font.widthOfTextAtSize(candidate, fontSize) > max && current) { lines.push(current); current = word; }
    else current = candidate;
  }
  if (current) lines.push(current);
  return lines;
}
function textBlock(text, font = regular, fontSize = 10, color = ink, gap = 15) {
  // Standard PDF fonts do not cover all Unicode punctuation; normalize source typography.
  const safe = text.replace(/[\u2018\u2019]/g, "'").replace(/[\u201c\u201d]/g, '"').replace(/[\u2013\u2014]/g, '-').replace(/[^\x20-\x7e]/g, '?');
  for (const row of wrap(safe, font, fontSize)) line(row, font, fontSize, color, gap);
}

newPage();
y = 545;
line('JAVA / BACKEND', bold, 12, accent, 36);
textBlock('Top 200 Java Backend Developer', bold, 29, ink, 38);
textBlock('Interview Questions and Answers', bold, 29, ink, 38);
y -= 25;
line('3-4 Years Experience  |  Java 17/21 + Spring Boot 3', regular, 12, muted, 24);
line('A practical interview-preparation book', regular, 11, muted);

newPage();
line('CONTENTS', bold, 21, ink, 34);
for (let i = 0; i < chapterNames.length; i++) {
  const heading = chapters[i].split('\n')[0].replace(/^# /, '');
  textBlock(heading, regular, 11, ink, 25);
}
y -= 15;
for (const extra of extras) textBlock(extra.split('\n')[0].replace(/^# /, ''), regular, 11, muted, 23);

for (const source of [...chapters, ...extras]) {
  newPage();
  let inCode = false;
  for (const raw of source.split('\n')) {
    const row = raw.trim();
    if (!row) { y -= 6; continue; }
    if (row.startsWith('```')) { inCode = !inCode; y -= 5; continue; }
    if (row.startsWith('# ')) { textBlock(row.slice(2), bold, 18, accent, 24); y -= 12; continue; }
    if (row.startsWith('## ')) { if (y < 125) newPage(); textBlock(row.slice(3), bold, 13, ink, 20); y -= 6; continue; }
    if (row.startsWith('### ')) { textBlock(row.slice(4), bold, 11, accent, 18); continue; }
    const cleaned = row.replace(/\*\*/g, '').replace(/`/g, '');
    textBlock(cleaned, inCode ? mono : regular, inCode ? 8 : 9.5, inCode ? muted : ink, inCode ? 12 : 14);
  }
}
const pages = pdf.getPages();
pages.forEach((p, i) => {
  p.drawLine({ start: { x: 56, y: 42 }, end: { x: 539, y: 42 }, thickness: .5, color: rgb(.78, .8, .8) });
  p.drawText('JAVA BACKEND INTERVIEW BOOK', { x: 56, y: 27, font: bold, size: 7, color: muted });
  p.drawText(`${i + 1}`, { x: 525, y: 27, font: regular, size: 8, color: muted });
});
const bytes = await pdf.save();
const output = path.join(root, 'Java_Backend_Top_200_Interview_Questions.pdf');
fs.writeFileSync(output, bytes);
const check = fs.readFileSync(output);
if (check.length < 10000 || check.subarray(0, 5).toString() !== '%PDF-') throw new Error('PDF size/signature check failed.');
console.log(`Built ${output} (${check.length} bytes, ${pages.length} pages).`);