import fs from 'fs';

const filePath = 'src/translations.ts';
let content = fs.readFileSync(filePath, 'utf8');

// Extract EN object
const enStart = content.indexOf('  EN: {');
const enEnd = content.indexOf('  },', enStart);
const enText = content.slice(enStart, enEnd + 3);

// Parse EN object roughly
const enPairs = {};
const lines = enText.split('\n');
for (const line of lines) {
  const match = line.match(/^\s+([^:]+):\s*"([^"]+)",?$/);
  if (match) {
    enPairs[match[1]] = match[2];
  }
}

// Extract KU object
const kuStart = content.indexOf('  KU: {');
const kuEnd = content.indexOf('  },', kuStart);
const kuText = content.slice(kuStart, kuEnd + 3);

const kuPairs = {};
const kuLines = kuText.split('\n');
for (const line of kuLines) {
  const match = line.match(/^\s+([^:]+):\s*"([^"]+)",?$/);
  if (match) {
    kuPairs[match[1]] = match[2];
  }
}

// Reconstruct KU object using EN as template
let newKuText = '  KU: {\n';
for (const key in enPairs) {
  const value = kuPairs[key] || enPairs[key];
  newKuText += `    ${key}: "${value}",\n`;
}
newKuText += '  },';

const newContent = content.replace(kuText, newKuText);
fs.writeFileSync(filePath, newContent);
console.log('Fixed KU section in translations.ts');
