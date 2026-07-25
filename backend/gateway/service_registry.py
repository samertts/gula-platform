services = {}


def register(name, url):
    services[name] = url


def get(name):
    return services.get(name)


def list_services():
    return services
