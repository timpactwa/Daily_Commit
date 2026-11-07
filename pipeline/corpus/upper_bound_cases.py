TOPIC = 'binary-search'
FUNCTION = 'upper_bound'
EDITION = 'research-2026-11'
QUESTION_LIMIT = 3
DIFFICULTY_OFFSET = 0
PROMPT = 'In a sorted list, return the first index whose value exceeds target, or len(nums). Tap the buggy line.'
CASES = [(([], 1), 0),
 (([1], 1), 1),
 (([1], 0), 0),
 (([1], 2), 1),
 (([1, 2, 2, 2, 4], 2), 4),
 (([1, 2, 4], 3), 2),
 (([1, 2, 4], 9), 3),
 (([-3, -1, 0], -2), 1),
 (([2, 2], 2), 2)]
