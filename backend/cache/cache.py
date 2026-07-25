import redis


def get_cache():

    return redis.Redis(host="localhost", port=6379, decode_responses=True)
