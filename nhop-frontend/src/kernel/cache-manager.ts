
import { openDB } from "idb";

let db:any;

export async function initCache(){

  db = await openDB("nhop-cache",2,{
    upgrade(db,oldVersion){

      if(oldVersion < 1)
        db.createObjectStore("patients");

      if(oldVersion < 2)
        db.createObjectStore("meta");
    }
  });
}

export async function cacheSet(store:string,key:string,value:any){

  await db.put(store,{
    value,
    ts:Date.now()
  },key);
}

export async function cacheGet(store:string,key:string,ttl=300000){

  const record = await db.get(store,key);

  if(!record) return null;

  if(Date.now()-record.ts > ttl)
    return null;

  return record.value;
}
