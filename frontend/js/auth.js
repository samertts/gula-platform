async function login(){

let username=document.getElementById("username").value
let password=document.getElementById("password").value

let r=await fetch("/api/login",{

method:"POST",

headers:{
"Content-Type":"application/json"
},

body:JSON.stringify({
username,
password
})

})

let d=await r.json()

localStorage.token=d.token

window.location="/"

}
