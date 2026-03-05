const fs = require("fs");
const path = require("path");

function loadModules(app) {
  const modulesPath = path.join(__dirname, "..");

  const folders = fs.readdirSync(modulesPath);

  folders.forEach((folder) => {
    const modulePath = path.join(modulesPath, folder);

    // skip core and queue folders
    if (folder === "core" || folder === "queue" || folder === "audit") {
      return;
    }

    const routesFile = path.join(modulePath, `${folder}.routes.js`);

    if (fs.existsSync(routesFile)) {
      try {
        const routes = require(routesFile);

        app.use(`/api/${folder}`, routes);

        console.log(`Module loaded: ${folder}`);
      } catch (err) {
        console.error(`Failed loading module ${folder}`, err);
      }
    }
  });
}

module.exports = { loadModules };
