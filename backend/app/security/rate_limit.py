
import time

requests={}

def check(ip):

    now=time.time()

    if ip not in requests:

        requests[ip]=[]

    requests[ip]=[t for t in requests[ip] if now-t<60]

    if len(requests[ip])>100:

        return False

    requests[ip].append(now)

    return True

