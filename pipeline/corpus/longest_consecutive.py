def longest_consecutive(nums):
    values = set(nums)
    best = 0
    for value in values:
        if value - 1 not in values:
            current = value
            length = 1
            while current + 1 in values:
                current += 1
                length += 1
            best = max(best, length)
    return best
