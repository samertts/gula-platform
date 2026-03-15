const ws = new WebSocket("wss://"+location.host+"/ws");

ws.onmessage = function(event){

let data = JSON.parse(event.data)

if(data.type==="stats"){

document.getElementById("patients").innerText=data.patients
document.getElementById("samples").innerText=data.samples
document.getElementById("tests").innerText=data.tests
document.getElementById("critical").innerText=data.critical

}

}
