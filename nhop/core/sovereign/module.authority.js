const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

const TRUSTED_FILE = path.join(__dirname, "../../trusted.modules.json");

function loadTrustedModules() {
  if (!fs.existsSync(TRUSTED_FILE)) {
    return [];
  }

  return JSON.parse(fs.readFileSync(TRUSTED_FILE));
}

function hashFile(filePath) {
  const content = fs.readFileSync(filePath);
  return crypto.createHash("sha256").update(content).digest("hex");
}

function verifyModule(modulePath) {
  const trusted = loadTrustedModules();

  const manifestPath = path.join(modulePath, "module.manifest.json");

  if (!fs.existsSync(manifestPath)) {
    throw new Error("Module manifest missing");
  }

  const manifest = JSON.parse(fs.readFileSync(manifestPath));

  const entry = path.join(modulePath, manifest.entry);

  const hash = hashFile(entry);

  const approved = trusted.find(
    m => m.name === manifest.name && m.hash === hash
  );

  if (!approved) {
    throw new Error(`Module not trusted: ${manifest.name}`);
  }

  return manifest;
}

module.exports = {
  verifyModule
};
