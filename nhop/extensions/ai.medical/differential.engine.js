
"use strict";

/*
==========================================================
DIFFERENTIAL DIAGNOSIS ENGINE
Bayesian Clinical Reasoning
Explainable Medical AI
==========================================================
*/

const DISEASE_MODEL = {

  diabetes: {
    prior: 0.12,
    evidence: {
      glucose_high: 4.5,
      obesity: 2.0,
      fatigue: 1.5
    }
  },

  infection: {
    prior: 0.18,
    evidence: {
      wbc_high: 3.5,
      fever: 4.0,
      crp_high: 3.0
    }
  },

  anemia: {
    prior: 0.10,
    evidence: {
      hemoglobin_low: 5.0,
      fatigue: 2.2,
      pallor: 2.5
    }
  }

};

/* --------------------------------------------------
   DETECT CLINICAL EVIDENCE
-------------------------------------------------- */

function extractEvidence(data){

  const evidence = [];

  if(data.glucose > 180)
    evidence.push("glucose_high");

  if(data.wbc > 11000)
    evidence.push("wbc_high");

  if(data.hemoglobin < 10)
    evidence.push("hemoglobin_low");

  if(data.fever === true)
    evidence.push("fever");

  return evidence;
}

/* --------------------------------------------------
   BAYESIAN UPDATE
-------------------------------------------------- */

function bayesianScore(disease, evidenceList){

  let score = disease.prior;
  const explanation = [];

  for(const ev of evidenceList){

    const likelihood =
      disease.evidence[ev];

    if(likelihood){

      score *= likelihood;

      explanation.push({
        evidence: ev,
        impact: likelihood
      });
    }
  }

  return { score, explanation };
}

/* --------------------------------------------------
   NORMALIZE PROBABILITIES
-------------------------------------------------- */

function normalize(results){

  const total =
    results.reduce((s,r)=>s+r.score,0) || 1;

  return results.map(r=>({
    ...r,
    probability:
      Number((r.score/total).toFixed(3))
  }));
}

/* --------------------------------------------------
   MAIN ENGINE
-------------------------------------------------- */

async function runDifferential(input){

  const evidence =
    extractEvidence(input);

  const results = [];

  for(const [name,model]
        of Object.entries(DISEASE_MODEL)){

    const {score, explanation} =
      bayesianScore(model,evidence);

    results.push({
      disease:name,
      score,
      explanation
    });
  }

  const ranked =
    normalize(results)
      .sort((a,b)=>b.probability-a.probability);

  return {
    evidence,
    differential: ranked,
    generatedAt: new Date().toISOString(),
    disclaimer:
      "AI-generated clinical support, not diagnosis"
  };
}

module.exports = {
  runDifferential
};

