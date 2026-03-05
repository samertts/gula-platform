
"use strict";

/*
AI EXECUTION SANDBOX
Isolated Worker Runtime
*/

const { Worker } = require("worker_threads");
const path = require("path");

function runAISafely(payload) {
  return new Promise((resolve, reject) => {

    const worker = new Worker(`
      const { parentPort, workerData } = require("worker_threads");

      function medicalAI(input) {

        // --- SIMULATED MEDICAL REASONING ---
        if(!input.symptoms)
          return { error: "No symptoms provided" };

        const risk =
          input.symptoms.includes("chest pain")
            ? "HIGH"
            : "LOW";

        return {
          triage: risk,
          advice:
            risk === "HIGH"
              ? "Immediate medical evaluation required"
              : "Monitor symptoms"
        };
      }

      try {
        const result = medicalAI(workerData);
        parentPort.postMessage({ ok:true, result });
      } catch(e){
        parentPort.postMessage({ ok:false, error:e.message });
      }

    `,{
      eval:true,
      workerData: payload
    });

    const timeout = setTimeout(()=>{
      worker.terminate();
      reject(new Error("AI execution timeout"));
    },3000);

    worker.on("message",(msg)=>{
      clearTimeout(timeout);
      resolve(msg);
    });

    worker.on("error",reject);
  });
}

module.exports = { runAISafely };
