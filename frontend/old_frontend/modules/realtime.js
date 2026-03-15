
async function realtime(){

try{

let r=await fetch("/api/dashboard")
let d=await r.json()

if(document.getElementById("patients"))
patients.innerText=d.patients

}catch(e){}

}

setInterval(realtime,15000)

