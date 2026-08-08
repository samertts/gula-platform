import fs from 'fs';

const filePath = 'src/translations.ts';
let content = fs.readFileSync(filePath, 'utf8');

const kuStart = content.indexOf('  KU: {');
const trStart = content.indexOf('  TR: {', kuStart);

const kuSection = content.slice(kuStart, trStart);
const fixedKuSection = kuSection.replace('dir: "ltr"', 'dir: "rtl"');

const newContent = content.replace(kuSection, fixedKuSection);
fs.writeFileSync(filePath, newContent);
console.log('Fixed KU dir');
