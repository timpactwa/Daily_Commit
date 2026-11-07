TOPIC = 'hash-maps'
FUNCTION = 'subarray_sum_count'
EDITION = 'research-2026-11'
QUESTION_LIMIT = 3
DIFFICULTY_OFFSET = 300
PROMPT = 'Count nonempty contiguous subarrays whose sum equals target, including negative values. Tap the buggy line.'
CASES = [(([], 0), 0),
 (([1], 1), 1),
 (([1], 2), 0),
 (([0, 0], 0), 3),
 (([1, 1, 1], 2), 2),
 (([1, -1, 0], 0), 3),
 (([3, 4, 7, 2, -3, 1, 4, 2], 7), 4),
 (([-1, -1, 1], 0), 1),
 (([2, -2, 2], 2), 3)]
