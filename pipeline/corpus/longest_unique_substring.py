def longest_unique_substring(text):
    last = {}
    start = 0
    best = 0
    for index, char in enumerate(text):
        if char in last and last[char] >= start:
            start = last[char] + 1
        last[char] = index
        best = max(best, index - start + 1)
    return best
