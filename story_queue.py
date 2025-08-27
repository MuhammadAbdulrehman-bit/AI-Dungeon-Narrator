import heapq

MAX_SIZE = 10
priority_memory = []

def add_to_queue(priority, fact):
    item = (priority, fact)

    if len(priority_memory) < MAX_SIZE:
        heapq.heappush(priority_memory, item)
    else:
        lowest = priority_memory[0]
        if item > lowest:
            heapq.heappushpop(priority_memory. item)


def get_priority_memory():
    return[fact for priority, fact in sorted(priority_memory, reverse=True)]

def clear_priority_memory():
    priority_memory.clear()

def remove_by_index(index):
    if 0<= index < len(priority_memory):
        priority_memory.pop(index)
        return True
    return False

def list_priority_memory():
    """
    Returns list of all (priority, memory) tuples, for display/debugging.
    """
    return list(priority_memory)

