import heapq

sample_queue = []


def add_sample(sample_id, priority):

    heapq.heappush(sample_queue, (priority, sample_id))


def get_next_sample():

    return heapq.heappop(sample_queue)
