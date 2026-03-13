
def analyze(test,value):

    if test=="glucose":

        if value>140:

            return "ارتفاع محتمل في السكر"

    if test=="hb":

        if value<11:

            return "قد يكون فقر دم"

    return "القيمة ضمن الطبيعي"

