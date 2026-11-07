def selection_sort(nums):
    result = nums[:]
    n = len(result)
    i = 0
    while i < n - 1:
        smallest = i
        j = i + 1
        while j < n:
            if result[j] < result[smallest]:
                smallest = j
            j += 1
        result[i], result[smallest] = (result[smallest], result[i])
        i += 1
    return result
