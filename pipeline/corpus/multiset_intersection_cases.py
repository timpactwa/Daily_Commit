TOPIC = 'hash-maps'
FUNCTION = 'multiset_intersection'
EDITION = 'research-2026-11'
QUESTION_LIMIT = 3
DIFFICULTY_OFFSET = 0
PROMPT = 'Return the multiset intersection in right-list order. Each value can appear only as often as in both lists. Tap the buggy line.'
CASES = [(([], []), []),
 (([1], []), []),
 (([], [1]), []),
 (([1, 1, 2], [1, 2, 1, 1]), [1, 2, 1]),
 (([3, 2], [2, 3, 2]), [2, 3]),
 (([1, 2], [3, 4]), []),
 (([-1, 0, -1], [-1, -1, 0]), [-1, -1, 0]),
 (([4, 4, 4], [4]), [4])]
