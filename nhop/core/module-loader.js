const fs = require("fs");
const path = require("path");

module.exports = function loadModules(app) {
  const modulesPath = path.join(__dirname, "../modules");

  const modules = fs.readdirSync(modulesPath);

  modules.forEach((name) => {
    const moduleEntry = path.join(modulesPath, name, "module.js");

    if (!fs.existsSync(moduleEntry)) return;

    const loaded = require(moduleEntry);

    // support both export styles
    if (typeof loaded === "function") {
      loaded(app);
      console.log(`Module loaded: ${name}`);
    } else if (loaded && typeof loaded.register === "function") {
      loaded.register(app);
      console.log(`Module loaded: ${name}`);
    } else {
      console.log(`Module skipped: ${name}`);
    }
  });
};
