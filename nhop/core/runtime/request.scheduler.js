const { isOverloaded } = require("./load.brain");

function scheduler(req, res, next) {

  if (isOverloaded()) {
    return res.status(503).json({
      error: "System busy, retry shortly"
    });
  }

  next();
}

module.exports = scheduler;
