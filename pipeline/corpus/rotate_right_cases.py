TOPIC = 'arrays-strings'
FUNCTION = 'rotate_right'
EDITION = 'continuation-2026-11'
QUESTION_LIMIT = 5
DIFFICULTY_OFFSET = 200
PROMPT = 'Return a new list rotated right by nonnegative k places; empty input gives []. Tap the buggy line.'
CASES = [(([], 0), []),
 (([], 7), []),
 (([1], 3), [1]),
 (([1, 2, 3], 0), [1, 2, 3]),
 (([1, 2, 3], 1), [3, 1, 2]),
 (([1, 2, 3], 2), [2, 3, 1]),
 (([1, 2, 3], 3), [1, 2, 3]),
 (([1, 2, 3], 8), [2, 3, 1]),
 (([-1, 0, 4, 4], 1), [4, -1, 0, 4]),
 (([8, 3], 5), [3, 8]),
 (([0, 1, 2, 3, 4], 4), [1, 2, 3, 4, 0])]
