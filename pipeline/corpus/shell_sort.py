def shell_sort(nums):
    result = nums[:]
    gap = len(result) // 2
    while gap > 0:
        for index in range(gap, len(result)):
            value = result[index]
            cursor = index
            while cursor >= gap and result[cursor - gap] > value:
                result[cursor] = result[cursor - gap]
                cursor -= gap
            result[cursor] = value
        gap = gap // 2
    return result
