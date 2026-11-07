def longest_balanced_binary(nums):
    balance = 0
    first = {0: -1}
    best = 0
    for i, value in enumerate(nums):
        balance += 1 if value == 1 else -1
        if balance in first:
            length = i - first[balance]
            if length > best:
                best = length
        else:
            first[balance] = i
    return best
