
"use strict";

const sandbox = require("./ai.sandbox");

async function analyzeMedicalCase(data){

  const result = await sandbox.runAISafely(data);

  if(!result.ok)
    throw new Error(result.error);

  return result.result;
}

module.exports = {
  analyzeMedicalCase
};
