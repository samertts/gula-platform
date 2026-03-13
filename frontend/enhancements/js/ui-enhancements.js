document.addEventListener("DOMContentLoaded",function(){

console.log("GULA UI enhancements loaded");

const buttons=document.querySelectorAll("button");

buttons.forEach(btn=>{
btn.addEventListener("click",()=>{
btn.style.opacity="0.8";
setTimeout(()=>btn.style.opacity="1",200);
});
});

});
