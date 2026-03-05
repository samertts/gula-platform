function memoryGuard() {

  const used = process.memoryUsage().heapUsed / 1024 / 1024;

  if (used > 700) {
    console.warn("High memory usage:", used.toFixed(2), "MB");
  }
}

setInterval(memoryGuard, 5000).unref();

module.exports = {};
