def first_occurrence(nums, target):
    lo, hi = (0, len(nums) - 1)
    result = -1
    while lo <= hi:
        mid = (lo + hi) // 2
        if nums[mid] == target:
            result = mid
            hi = mid - 1
        elif nums[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return result
