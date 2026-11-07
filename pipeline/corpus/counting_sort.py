def counting_sort(nums):
    if not nums:
        return []
    low = min(nums)
    high = max(nums)
    counts = [0] * (high - low + 1)
    for value in nums:
        counts[value - low] += 1
    result = []
    for offset, count in enumerate(counts):
        for _ in range(count):
            result.append(offset + low)
    return result
