/*
========================================
NHOP EVENT BUS
Lightweight realtime communication core
========================================
*/

type EventHandler = (data:any)=>void;

class EventBus {

  private events: Map<string, EventHandler[]> = new Map();

  subscribe(event:string, handler:EventHandler){

    if(!this.events.has(event)){
      this.events.set(event,[]);
    }

    this.events.get(event)!.push(handler);
  }

  publish(event:string, data:any){

    const handlers = this.events.get(event);

    if(!handlers) return;

    handlers.forEach(h=>{
      try{
        h(data);
      }catch(err){
        console.error("Event handler error",err);
      }
    });
  }

}

export function initEventBus(){
  return new EventBus();
}
