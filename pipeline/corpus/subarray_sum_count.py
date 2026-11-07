def subarray_sum_count(nums, target):
    seen = {0: 1}
    total = 0
    count = 0
    for value in nums:
        total += value
        count += seen.get(total - target, 0)
        seen[total] = seen.get(total, 0) + 1
    return count
