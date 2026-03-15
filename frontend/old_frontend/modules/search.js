
function search(){

let input=document.getElementById("search")

if(!input) return

input.addEventListener("keyup",function(){

let q=this.value.toLowerCase()

document.querySelectorAll(".card").forEach(c=>{

c.style.display = c.innerText.toLowerCase().includes(q) ? "block":"none"

})

})

}

setTimeout(search,1000)

