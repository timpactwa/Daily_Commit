def running_max(nums):
    if not nums:
        return []
    best = nums[0]
    result = [nums[0]]
    i = 1
    while i < len(nums):
        if nums[i] > best:
            best = nums[i]
        result.append(best)
        i += 1
    return result
