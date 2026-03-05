
"use strict";

module.exports.register = async function(capabilities){

  const { router, logger } = capabilities;

  router.get("/ai/ping",(req,res)=>{
    res.json({ ok:true });
  });

  logger.info("AI Assistant extension loaded");
};
