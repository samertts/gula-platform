import fs from 'fs';

const filePath = 'src/translations.ts';
let content = fs.readFileSync(filePath, 'utf8');

const targetStart = '    biometricFailed: "Biometric verification failed. Please try again.",\n  },\n prescriptions: "Reçeteler",';
const targetEnd = '    analyzeReport: "Analyzing...",\n  },\n  SY: {';

// It might be easier to find the SY start and search backwards for the first }, and then another },
const syStart = '  SY: {';
const syIndex = content.indexOf(syStart);

if (syIndex !== -1) {
  // Find the closing brace just before SY
  const lastClose = content.lastIndexOf('},', syIndex);
  if (lastClose !== -1) {
    // Find the one before it
    const secondLastClose = content.lastIndexOf('},', lastClose - 1);
    if (secondLastClose !== -1) {
      // Find biometricFailed before secondLastClose
      const bioBefore = content.lastIndexOf('biometricFailed:', secondLastClose);
      if (bioBefore !== -1) {
        // We want to keep from bioBefore up to secondLastClose+2 (the },)
        // And then skip until syIndex
        const part1 = content.slice(0, secondLastClose + 2);
        const part2 = content.slice(syIndex);
        
        fs.writeFileSync(filePath, part1 + '\n' + part2);
        console.log('Fixed translations.ts - removed garbage block');
      } else {
        console.log('Could not find biometricFailed before second last close');
      }
    } else {
      console.log('Could not find second last close');
    }
  } else {
    console.log('Could not find last close');
  }
} else {
  console.log('Could not find SY: {');
}
