import fs from 'fs';
const content = fs.readFileSync('src/translations.ts', 'utf8');
const opens = (content.match(/{/g) || []).length;
const closes = (content.match(/}/g) || []).length;
console.log(`Opens: ${opens}, Closes: ${closes}`);
