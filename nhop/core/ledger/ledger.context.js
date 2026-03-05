
"use strict";

/*
==================================================
NHOP LEDGER CONTEXT
Ledger Enforcement Tracker
==================================================
Tracks if request produced a ledger event
==================================================
*/

const requests = new Map();

/* ================================================
   START REQUEST TRACKING
================================================ */

function startRequest(requestId){

  requests.set(requestId,{
    committed:false,
    startedAt:Date.now()
  });
}

/* ================================================
   MARK LEDGER COMMIT
================================================ */

function markCommitted(requestId){

  const ctx = requests.get(requestId);

  if(ctx){
    ctx.committed = true;
  }
}

/* ================================================
   VERIFY REQUEST
================================================ */

function verify(requestId){

  const ctx = requests.get(requestId);

  requests.delete(requestId);

  return ctx?.committed === true;
}

/* ================================================
   CLEANUP (SAFETY)
================================================ */

setInterval(()=>{

  const now = Date.now();

  for(const [id,ctx] of requests){

    if(now - ctx.startedAt > 60000){
      requests.delete(id);
    }
  }

},30000);

/* ================================================
   EXPORTS
================================================ */

module.exports = Object.freeze({
  startRequest,
  markCommitted,
  verify
});
