
"use strict";

/*
==================================================
NHOP SECURE ROUTER
Forces ledger enforcement on write routes
==================================================
*/

const ledgerContext =
  require("../ledger/ledger.context");

function wrap(handler){

  return async (req,res,next)=>{

    try{

      await handler(req,res,next);

      const ok =
        ledgerContext.verify(req.requestId);

      if(!ok){
        throw new Error(
          "Ledger event required but missing"
        );
      }

    }catch(err){
      next(err);
    }
  };
}

function createSecureRouter(app){

  return Object.freeze({

    get:(path,handler)=>
      app.get(path,handler),

    post:(path,handler)=>
      app.post(path,wrap(handler)),

    put:(path,handler)=>
      app.put(path,wrap(handler)),

    delete:(path,handler)=>
      app.delete(path,wrap(handler))
  });
}

module.exports = createSecureRouter;
