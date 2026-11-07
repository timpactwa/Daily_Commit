def recursive_search(nums, target, lo, hi):
    if lo > hi:
        return -1
    mid = (lo + hi) // 2
    if nums[mid] == target:
        return mid
    if nums[mid] < target:
        return recursive_search(nums, target, mid + 1, hi)
    return recursive_search(nums, target, lo, mid - 1)
