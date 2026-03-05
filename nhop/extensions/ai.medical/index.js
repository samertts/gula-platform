
"use strict";

/*
==========================================================
NHOP MEDICAL AI EXTENSION
Sovereign Clinical Intelligence Layer
==========================================================

Capabilities:
- Event-driven clinical reasoning
- Bayesian differential diagnosis
- Temporal medical memory
- Safe AI execution
- Explainable outputs
==========================================================
*/

const aiKernel = require("./ai.kernel");
const clinicalReasoner = require("./clinical.reasoner");
const differentialEngine = require("./differential.engine");

/* -------------------------------------------------------
   SAFE EXECUTION WRAPPER
------------------------------------------------------- */

async function safeExecute(logger, fn) {

  try {

    return await Promise.race([
      fn(),
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error("AI timeout")), 5000)
      )
    ]);

  } catch (err) {

    logger.error("AI execution failure", {
      error: err.message
    });

    return {
      error: true
    };
  }
}

/* =======================================================
   EXTENSION REGISTER
======================================================= */

module.exports.register = async function (capabilities) {

  const {
    router,
    logger,
    events
  } = capabilities;

  logger.info("Medical AI Extension booting");

  /* ---------------------------------------------------
     HEALTH CHECK
  --------------------------------------------------- */

  router.get("/ai/ping", (req, res) => {
    res.json({
      ai: "medical",
      status: "active"
    });
  });

  /* ---------------------------------------------------
     BASIC SAFE ANALYSIS
  --------------------------------------------------- */

  router.post("/ai/analyze", async (req, res) => {

    const input = req.body || {};

    const result = await safeExecute(
      logger,
      () => aiKernel.safeAnalyze(input)
    );

    if (result?.error) {
      return res.status(500).json({
        ok: false,
        error: "analysis_failed"
      });
    }

    res.json({
      ok: true,
      analysis: result
    });
  });

  /* ---------------------------------------------------
     DIFFERENTIAL DIAGNOSIS (Bayesian Engine)
  --------------------------------------------------- */

  router.post("/ai/differential", async (req, res) => {

    const input = req.body || {};

    const result = await safeExecute(
      logger,
      () => differentialEngine.runDifferential(input)
    );

    if (result?.error) {
      return res.status(500).json({
        ok: false,
        error: "differential_failed"
      });
    }

    res.json({
      ok: true,
      result
    });
  });

  /* ---------------------------------------------------
     EVENT-DRIVEN CLINICAL INTELLIGENCE
  --------------------------------------------------- */

  if (events?.subscribe) {

    events.subscribe(
      "lab.result.created",
      async (payload) => {

        logger.info("AI received lab event", {
          patientId: payload?.patientId
        });

        await safeExecute(
          logger,
          () =>
            clinicalReasoner.processObservation(
              events,
              logger,
              payload
            )
        );
      }
    );
  }

  /* ---------------------------------------------------
     CLINICAL INSIGHT OBSERVER (optional future chaining)
  --------------------------------------------------- */

  if (events?.subscribe) {

    events.subscribe(
      "clinical.insight.created",
      async (insight) => {

        logger.info("Clinical insight generated", {
          patientId: insight?.patientId,
          risk: insight?.risk
        });

      }
    );
  }

  logger.info("Medical AI Extension fully activated");
};
