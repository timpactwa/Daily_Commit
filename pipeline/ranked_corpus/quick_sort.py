def quick_sort(nums, lo=0, hi=None):
    if hi is None:
        hi = len(nums) - 1
    if lo >= hi:
        return nums
    pivot = nums[hi]
    i = lo
    for j in range(lo, hi):
        if nums[j] < pivot:
            nums[i], nums[j] = (nums[j], nums[i])
            i += 1
    nums[i], nums[hi] = (nums[hi], nums[i])
    quick_sort(nums, lo, i - 1)
    quick_sort(nums, i + 1, hi)
    return nums
