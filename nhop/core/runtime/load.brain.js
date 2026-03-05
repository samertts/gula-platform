const os = require("os");

let state = {
  overloaded: false
};

function checkLoad() {

  const cpuLoad = os.loadavg()[0];
  const cpuCount = os.cpus().length;

  state.overloaded = cpuLoad > cpuCount * 1.2;
}

setInterval(checkLoad, 2000).unref();

function isOverloaded() {
  return state.overloaded;
}

module.exports = { isOverloaded };
