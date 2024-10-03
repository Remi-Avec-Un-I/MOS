def chunk(list_a, chunk_size):
    for i in range(0, len(list_a), chunk_size):
        yield list_a[i:i + chunk_size]

def find_nth_occurrence(string: str, substring: str, n: int) -> int:
    start = 0
    count = 0
    
    while count < n:
        start = string.find(substring, start)
        if start == -1:
            return -1
        start += 1
        count += 1
    
    return start - 1
