TOPIC = 'hash-maps'
FUNCTION = 'count_pairs_with_sum'
EDITION = 'continuation-2026-11'
QUESTION_LIMIT = 5
DIFFICULTY_OFFSET = 50
PROMPT = 'Count index pairs i < j whose integer values sum to target, including duplicates. Tap the buggy line.'
CASES = [(([], 0), 0),
 (([1], 2), 0),
 (([1, 1], 2), 1),
 (([1, 1, 1], 2), 3),
 (([1, 2, 3, 4], 5), 2),
 (([0, 0, 0, 0], 0), 6),
 (([-2, -1, 0, 1, 2], 0), 2),
 (([3, 3, 3, 3], 6), 6),
 (([1, 2, 2, 3], 4), 2),
 (([2, 4, 6], 1), 0),
 (([-1, -1, 2, 2], 1), 4),
 (([5, 0, 5, 0], 5), 4)]
