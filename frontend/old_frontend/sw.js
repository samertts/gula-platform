
self.addEventListener("install",(e)=>{

e.waitUntil(

caches.open("gula").then(cache=>{

return cache.addAll([

"/",
"/index.html"

])

})

)

})
