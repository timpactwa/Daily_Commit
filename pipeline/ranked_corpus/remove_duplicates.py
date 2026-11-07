def remove_duplicates(nums):
    if not nums:
        return []
    write = 1
    for read in range(1, len(nums)):
        if nums[read] != nums[read - 1]:
            nums[write] = nums[read]
            write += 1
    return nums[:write]
