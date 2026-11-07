TOPIC = 'sorting'
FUNCTION = 'merge_sorted_unique'
EDITION = 'continuation-2026-11'
QUESTION_LIMIT = 5
DIFFICULTY_OFFSET = 200
PROMPT = 'Merge two sorted integer lists into a new sorted list containing each value once. Tap the buggy line.'
CASES = [(([], []), []),
 (([], [1]), [1]),
 (([1], []), [1]),
 (([1], [1]), [1]),
 (([1], [2]), [1, 2]),
 (([2], [1]), [1, 2]),
 (([1, 1, 3], [1, 2, 2]), [1, 2, 3]),
 (([-3, -1, 0], [-2, 0, 4]), [-3, -2, -1, 0, 4]),
 (([1, 2, 3], [4]), [1, 2, 3, 4]),
 (([4], [1, 2, 3]), [1, 2, 3, 4]),
 (([0, 0], [0, 0]), [0]),
 (([-5, -5, -1], [-5, -2, -1]), [-5, -2, -1])]
