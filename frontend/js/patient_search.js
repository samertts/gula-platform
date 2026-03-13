
function searchPatients(){

let input=document.getElementById("patientSearch")

if(!input)return

input.addEventListener("keyup",function(){

let q=this.value.toLowerCase()

document.querySelectorAll(".patient-row").forEach(row=>{

row.style.display=row.innerText.toLowerCase().includes(q)
?"block":"none"

})

})

}

setTimeout(searchPatients,500)

