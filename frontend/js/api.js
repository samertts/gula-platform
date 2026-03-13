
const API="/api"

async function api(path){

try{

let r=await fetch(API+path)
return r.json()

}catch(e){

return {}

}

}

