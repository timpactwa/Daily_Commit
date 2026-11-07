def recursive_count(nums, target):

    def count(lo, hi):
        if lo > hi:
            return 0
        mid = (lo + hi) // 2
        hit = 1 if nums[mid] == target else 0
        return hit + count(lo, mid - 1) + count(mid + 1, hi)
    return count(0, len(nums) - 1)
