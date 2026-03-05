
"use strict";

/*
NHOP CLINICAL OBSERVER
Event-driven medical signal listener
*/

const eventBus = require("../../core/events/event.bus");

function evaluateLab(result){

  if(!result) return;

  if(result.test === "glucose" && result.value > 200){
    console.warn("[CLINICAL ALERT] Possible hyperglycemia", result);
  }

  if(result.test === "wbc" && result.value > 15000){
    console.warn("[CLINICAL ALERT] Possible infection", result);
  }
}

function start(){

  eventBus.subscribe("lab.result.created", evaluateLab);

  console.log("Clinical observer active");
}

module.exports = {
  start
};
