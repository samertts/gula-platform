
function aliReza(){

window.aliRezaAnalyze=function(test,value){

let advice=""

if(test=="glucose" && value>140)
advice="ارتفاع محتمل في السكر"

if(test=="hb" && value<11)
advice="احتمال فقر دم"

if(advice!="")
alert("علي رضا:\n"+advice)

}

}

aliReza()

