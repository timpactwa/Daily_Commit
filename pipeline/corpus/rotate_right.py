def rotate_right(nums, k):
    if not nums:
        return []
    n = len(nums)
    k = k % n
    result = nums[:]

    def reverse(start, end):
        while start < end:
            result[start], result[end] = (result[end], result[start])
            start += 1
            end -= 1
    reverse(0, n - 1)
    reverse(0, k - 1)
    reverse(k, n - 1)
    return result
