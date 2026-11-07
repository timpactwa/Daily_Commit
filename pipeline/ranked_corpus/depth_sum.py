def depth_sum(items, depth=1):
    total = 0
    for item in items:
        if isinstance(item, list):
            total += depth_sum(item, depth + 1)
        else:
            total += item * depth
    return total
