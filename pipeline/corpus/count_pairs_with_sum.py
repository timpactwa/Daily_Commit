def count_pairs_with_sum(nums, target):
    seen = {}
    pairs = 0
    for value in nums:
        pairs += seen.get(target - value, 0)
        seen[value] = seen.get(value, 0) + 1
    return pairs
