import fs from 'fs';

const filePath = 'src/translations.ts';
let content = fs.readFileSync(filePath, 'utf8');

const targetLineStart = '    mfa: "تەئکیدکردنەوەی دوو ق';
const nextLine = '    appName: "GULA Platformu",';

const lines = content.split('\n');
const newLines = [];

for (let i = 0; i < lines.length; i++) {
  if (lines[i].includes(targetLineStart) && lines[i+1] && lines[i+1].includes(nextLine)) {
    newLines.push('    mfa: "تەئکیدکردنەوەی دوو قۆناغی",');
    newLines.push('  },');
    newLines.push('  TR: {');
  } else {
    newLines.push(lines[i]);
  }
}

fs.writeFileSync(filePath, newLines.join('\n'));
console.log('Fixed translations.ts');
