let healthy = true;

function setUnhealthy() {
  healthy = false;
}

function isHealthy() {
  return healthy;
}

module.exports = {
  setUnhealthy,
  isHealthy
};
