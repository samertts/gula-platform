const fs = require('node:fs');

const reportPath = process.env.NPM_AUDIT_REPORT || '/tmp/gula-mobile-expo-audit.json';
const report = JSON.parse(fs.readFileSync(reportPath, 'utf8'));
const vulnerabilities = report.vulnerabilities ?? {};
const metadata = report.metadata?.vulnerabilities ?? {};
const total = metadata.total ?? Object.keys(vulnerabilities).length;

if (total > 0) {
  const details = Object.values(vulnerabilities)
    .map((entry) => `${entry.severity}: ${entry.name}`)
    .join(', ');
  throw new Error(`Mobile dependency audit gate failed: ${details}`);
}

console.log(JSON.stringify({
  status: 'passed-zero-findings',
  info: metadata.info ?? 0,
  low: metadata.low ?? 0,
  moderate: metadata.moderate ?? 0,
  high: metadata.high ?? 0,
  critical: metadata.critical ?? 0,
  total,
}, null, 2));
