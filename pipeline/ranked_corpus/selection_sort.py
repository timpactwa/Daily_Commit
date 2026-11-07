def selection_sort(nums):
    result = nums[:]
    for i in range(len(result)):
        smallest = i
        for j in range(i + 1, len(result)):
            if result[j] < result[smallest]:
                smallest = j
        result[i], result[smallest] = (result[smallest], result[i])
    return result
