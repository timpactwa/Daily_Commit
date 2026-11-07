def max_depth(items):
    deepest = 0
    for item in items:
        if isinstance(item, list):
            deepest = max(deepest, max_depth(item))
    return deepest + 1
