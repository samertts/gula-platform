
import datetime

def log(action,user):

    return {

        "action":action,

        "user":user,

        "timestamp":datetime.datetime.utcnow()

    }

