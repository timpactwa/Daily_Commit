TOPIC = 'arrays-strings'
FUNCTION = 'prefix_sums'
EDITION = 'research-2026-11'
QUESTION_LIMIT = 3
DIFFICULTY_OFFSET = -25
PROMPT = 'Return prefix totals with an initial zero (empty input returns [0]). Tap the buggy line.'
CASES = [(([],), [0]),
 (([2, 1],), [0, 2, 3]),
 (([3, 1, 2],), [0, 3, 4, 6]),
 (([5, 4, 3, 2, 1],), [0, 5, 9, 12, 14, 15]),
 (([1, 2, 3],), [0, 1, 3, 6]),
 (([4, 4, 1, 4],), [0, 4, 8, 9, 13]),
 (([-3, 0, -1, 2],), [0, -3, -3, -4, -2]),
 (([0],), [0, 0]),
 (([2, -2, 2, -2],), [0, 2, 0, 2, 0])]
