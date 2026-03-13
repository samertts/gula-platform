
const GULA = {}

GULA.loadPage = async function(page){

const res = await fetch("/pages/"+page+".html")

const html = await res.text()

document.getElementById("gula-content").innerHTML = html

}

