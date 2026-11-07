def prefix_sums(nums):
    result = [0]
    total = 0
    for value in nums:
        total += value
        result.append(total)
    return result
