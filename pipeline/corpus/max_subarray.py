def max_subarray(nums):
    if not nums:
        return 0
    current = nums[0]
    best = nums[0]
    for value in nums[1:]:
        current = max(value, current + value)
        best = max(best, current)
    return best
