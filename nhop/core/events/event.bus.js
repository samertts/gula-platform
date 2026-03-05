
"use strict";

/*
NHOP EVENT BUS
Non-blocking internal communication layer
*/

const listeners = new Map();

function subscribe(event, handler){

  if(!listeners.has(event))
    listeners.set(event, []);

  listeners.get(event).push(handler);
}

function publish(event, payload){

  const subs = listeners.get(event);
  if(!subs) return;

  for(const handler of subs){

    setImmediate(()=>{

      try{
        handler(payload);
      }catch(e){
        console.error("[EVENT BUS ERROR]", e.message);
      }

    });
  }
}

module.exports = {
  subscribe,
  publish
};
