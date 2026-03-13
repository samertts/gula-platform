window.addEventListener("click",(e)=>{

if(e.target.tagName==="A"){

let href=e.target.getAttribute("href")

if(href.startsWith("/")){

e.preventDefault()

history.pushState({}, "", href)

location.reload()

}

}

})
