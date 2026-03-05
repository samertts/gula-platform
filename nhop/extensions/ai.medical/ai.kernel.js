
"use strict";

/*
AI Kernel Wrapper
Prevents blocking & isolates execution
*/

const engine = require("./ai.engine");

async function safeAnalyze(data){

  return new Promise((resolve)=>{

    setImmediate(()=>{

      try{
        const result = engine.analyze(data);
        resolve(result);
      }catch(e){
        resolve({
          riskLevel:"unknown",
          error:e.message
        });
      }

    });

  });
}

module.exports = {
  safeAnalyze
};
