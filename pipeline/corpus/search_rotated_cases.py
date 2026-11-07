TOPIC = 'binary-search'
FUNCTION = 'search_rotated'
EDITION = 'research-2026-11'
QUESTION_LIMIT = 3
DIFFICULTY_OFFSET = 275
PROMPT = 'Search a rotated ascending list of distinct integers. Return its index, or -1 if absent. Tap the buggy line.'
CASES = [(([], 2), -1),
 (([4], 4), 0),
 (([4], 2), -1),
 (([4, 5, 6, 7, 0, 1, 2], 0), 4),
 (([4, 5, 6, 7, 0, 1, 2], 3), -1),
 (([3, 1], 1), 1),
 (([1, 2, 3, 4], 4), 3),
 (([6, 7, 1, 2, 3, 4, 5], 7), 1),
 (([2, 3, 4, 5, 1], 5), 3)]
