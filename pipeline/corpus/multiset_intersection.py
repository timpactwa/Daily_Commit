def multiset_intersection(left, right):
    counts = {}
    for value in left:
        counts[value] = counts.get(value, 0) + 1
    common = []
    for value in right:
        if counts.get(value, 0) > 0:
            common.append(value)
            counts[value] -= 1
    return common
