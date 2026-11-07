def merge_sorted_unique(left, right):
    i = 0
    j = 0
    result = []
    while i < len(left) or j < len(right):
        if j == len(right) or (i < len(left) and left[i] <= right[j]):
            value = left[i]
            i += 1
        else:
            value = right[j]
            j += 1
        if not result or value != result[-1]:
            result.append(value)
    return result
