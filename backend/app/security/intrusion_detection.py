
failed_attempts={}

def detect(ip):

    if ip not in failed_attempts:

        failed_attempts[ip]=0

    failed_attempts[ip]+=1

    if failed_attempts[ip]>10:

        return "blocked"

    return "ok"

