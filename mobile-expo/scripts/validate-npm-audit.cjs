const fs = require('node:fs');

const reportPath = process.env.NPM_AUDIT_REPORT || '/tmp/gula-mobile-expo-audit.json';
const report = JSON.parse(fs.readFileSync(reportPath, 'utf8'));
const vulnerabilities = report.vulnerabilities ?? {};
const knownReviewedExpoChain = new Set([
  '@expo/cli',
  '@expo/config',
  '@expo/config-plugins',
  '@expo/metro',
  '@expo/metro-config',
  '@expo/prebuild-config',
  '@react-native/community-cli-plugin',
  'expo',
  'expo-asset',
  'expo-constants',
  'image-size',
  'metro',
  'metro-config',
  'metro-transform-worker',
  'postcss',
  'react-native',
  'uuid',
  'xcode',
]);

const critical = Object.values(vulnerabilities)
  .filter((entry) => entry.severity === 'critical')
  .map((entry) => entry.name);
const unknownHigh = Object.values(vulnerabilities)
  .filter((entry) => entry.severity === 'high' && !knownReviewedExpoChain.has(entry.name))
  .map((entry) => entry.name);

if (critical.length > 0 || unknownHigh.length > 0) {
  const details = [
    critical.length > 0 ? `critical: ${critical.join(', ')}` : null,
    unknownHigh.length > 0 ? `unapproved high: ${unknownHigh.join(', ')}` : null,
  ].filter(Boolean).join('; ');
  throw new Error(`Mobile dependency audit gate failed: ${details}`);
}

const metadata = report.metadata?.vulnerabilities ?? {};
console.log(JSON.stringify({
  status: 'passed-with-reviewed-expo-upstream-chain',
  critical: metadata.critical ?? 0,
  high: metadata.high ?? 0,
  moderate: metadata.moderate ?? 0,
  reviewedHigh: Object.values(vulnerabilities)
    .filter((entry) => entry.severity === 'high')
    .map((entry) => entry.name),
}, null, 2));
