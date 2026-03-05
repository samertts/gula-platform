
"use strict";

/*
==========================================================
CLINICAL REASONER ENGINE
Temporal Medical Intelligence
==========================================================
*/

const memory = require("./clinical.memory");

/* ---------------------------------------------------
   BUILD HYPOTHESIS
--------------------------------------------------- */

function buildHypothesis(data) {

  const hypotheses = [];

  if (data.glucose > 180)
    hypotheses.push("Possible Hyperglycemia");

  if (data.wbc > 11000)
    hypotheses.push("Possible Infection");

  if (data.hemoglobin < 10)
    hypotheses.push("Possible Anemia");

  return hypotheses;
}

/* ---------------------------------------------------
   RISK SCORE
--------------------------------------------------- */

function riskScore(hypotheses) {

  if (hypotheses.length >= 3) return "HIGH";
  if (hypotheses.length === 2) return "MEDIUM";
  if (hypotheses.length === 1) return "LOW";

  return "MINIMAL";
}

/* ---------------------------------------------------
   MAIN CLINICAL PROCESSOR
--------------------------------------------------- */

async function processObservation(events, logger, payload) {

  try {

    if (!payload) return;

    const patientId = payload.patientId || "unknown";

    /* ---------- STORE MEMORY ---------- */

    memory.storeResult(patientId, payload);

    const history =
      memory.getHistory(patientId);

    /* ---------- TREND ANALYSIS ---------- */

    const glucoseTrend =
      memory.analyzeTrend(history, "glucose");

    /* ---------- CLINICAL REASONING ---------- */

    const hypotheses =
      buildHypothesis(payload);

    if (glucoseTrend === "rising") {
      hypotheses.push(
        "Worsening metabolic control"
      );
    }

    const risk = riskScore(hypotheses);

    const insight = {
      patientId,
      hypotheses,
      trend: {
        glucose: glucoseTrend
      },
      risk,
      timestamp: new Date().toISOString()
    };

    logger.info(
      "Clinical reasoning generated",
      insight
    );

    /* ---------- EMIT INSIGHT EVENT ---------- */

    events?.emit?.(
      "clinical.insight.created",
      insight
    );

  } catch (err) {

    logger.error("Clinical reasoning failure", {
      error: err.message
    });
  }
}

module.exports = {
  processObservation
};
