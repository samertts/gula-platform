
async function loadPage(page){

let r=await fetch("/pages/"+page+".html")
let html=await r.text()

document.getElementById("content").innerHTML=html

}

loadPage("dashboard")

