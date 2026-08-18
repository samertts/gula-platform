const fs = require('node:fs');

const configPath = process.env.EXPO_CONFIG_PATH || '/tmp/gula-expo-config.json';
const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
const flags = config.extra?.gula;
const failures = [];

if (flags?.clinicalVoiceDraftOnly !== true) {
  failures.push('clinicalVoiceDraftOnly must be true');
}
if (flags?.audioPersistence !== false) {
  failures.push('audioPersistence must be false');
}
if (flags?.analyticsCapture !== false) {
  failures.push('analyticsCapture must be false');
}

const permissions = Array.isArray(config.android?.permissions) ? config.android.permissions : [];
const forbiddenPermissions = permissions.filter((permission) =>
  /FOREGROUND_SERVICE|BACKGROUND_AUDIO|RECORD_IN_BACKGROUND/i.test(permission),
);
if (forbiddenPermissions.length > 0) {
  failures.push(`background recording permissions are not allowed: ${forbiddenPermissions.join(', ')}`);
}

if (failures.length > 0) {
  throw new Error(`Unsafe Expo speech configuration:\n- ${failures.join('\n- ')}`);
}

console.log('Expo config safety invariants passed');
console.log(JSON.stringify({
  name: config.name,
  slug: config.slug,
  permissions,
  flags,
}, null, 2));
