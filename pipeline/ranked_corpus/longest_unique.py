def longest_unique(s):
    last = {}
    start = 0
    best_start = 0
    best_len = 0
    for i, ch in enumerate(s):
        if ch in last and last[ch] >= start:
            start = last[ch] + 1
        last[ch] = i
        if i - start + 1 > best_len:
            best_start = start
            best_len = i - start + 1
    return s[best_start:best_start + best_len]
