
"use strict";

const express = require("express");
const router = express.Router();
const aiKernel = require("./ai.kernel");

router.post("/analyze", async (req,res,next)=>{
  try{

    const output =
      await aiKernel.analyzeMedicalCase(req.body);

    res.json({
      success:true,
      result:output
    });

  }catch(err){
    next(err);
  }
});

module.exports = router;
