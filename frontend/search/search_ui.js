async function gulaSearch(){

const q=document.getElementById("searchInput").value

const res=await axios.get("/api/search?q="+q)

document.getElementById("searchResult").innerHTML=
JSON.stringify(res.data,null,2)

}
