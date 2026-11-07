def most_common(nums):
    counts = {}
    best = None
    best_count = 0
    for x in nums:
        counts[x] = counts.get(x, 0) + 1
        if counts[x] > best_count:
            best = x
            best_count = counts[x]
    return best
