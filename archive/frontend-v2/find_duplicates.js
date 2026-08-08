
import fs from 'fs';

const content = fs.readFileSync('src/translations.ts', 'utf8');

const languages = ['EN', 'AR', 'KU', 'TR', 'SY'];

languages.forEach(lang => {
    const startRegex = new RegExp(`^  ${lang}: \\{`, 'm');
    const endRegex = new RegExp(`^  \\},`, 'm');
    
    const startIndex = content.search(startRegex);
    if (startIndex === -1) return;
    
    // Find matching closing brace for this language
    let depth = 0;
    let endIndex = -1;
    for (let i = startIndex; i < content.length; i++) {
        if (content[i] === '{') depth++;
        if (content[i] === '}') depth--;
        if (depth === 1 && content[i] === '}' && content[i+1] === ',') {
            endIndex = i;
            break;
        }
    }
    
    if (endIndex === -1) return;
    
    const block = content.substring(startIndex, endIndex);
    const lines = block.split('\n');
    const keys = lines
        .map(line => line.trim())
        .filter(line => line.includes(':'))
        .map(line => line.split(':')[0].trim());
    
    const counts = {};
    keys.forEach(key => {
        counts[key] = (counts[key] || 0) + 1;
    });
    
    const duplicates = Object.entries(counts).filter(([key, count]) => count > 1);
    
    if (duplicates.length > 0) {
        console.log(`Duplicates in ${lang}:`);
        duplicates.forEach(([key, count]) => console.log(`  ${key}: ${count}`));
    }
});
