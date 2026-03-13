
blocked_ips=set()

def block(ip):

    blocked_ips.add(ip)

def allowed(ip):

    return ip not in blocked_ips

