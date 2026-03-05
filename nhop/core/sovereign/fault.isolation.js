function isolate(handler) {

  return async function(req, res, next) {

    try {
      await handler(req, res, next);
    } catch (err) {

      console.error("ISOLATED_ERROR:", err.message);

      return res.status(500).json({
        error: "Module isolated failure",
        isolated: true
      });
    }
  };
}

module.exports = isolate;
