
async function updateDashboard(){

try{

let r=await fetch("/dashboard")
let data=await r.json()

let patients=document.getElementById("patients")
let samples=document.getElementById("samples")
let tests=document.getElementById("tests")
let critical=document.getElementById("critical")

if(patients)patients.innerText=data.patients
if(samples)samples.innerText=data.samples
if(tests)tests.innerText=data.tests
if(critical)critical.innerText=data.critical

}catch(e){

console.log("realtime error")

}

}

setInterval(updateDashboard,10000)

