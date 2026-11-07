TOPIC = 'arrays-strings'
FUNCTION = 'running_max'
EDITION = 'continuation-2026-11'
QUESTION_LIMIT = 5
DIFFICULTY_OFFSET = -75
PROMPT = 'Return the maximum seen through each list position; empty input gives []. Tap the buggy line.'
CASES = [(([],), []),
 (([0],), [0]),
 (([4],), [4]),
 (([-5, -9, -2],), [-5, -5, -2]),
 (([1, 2, 3],), [1, 2, 3]),
 (([3, 2, 1],), [3, 3, 3]),
 (([2, 2, 2],), [2, 2, 2]),
 (([1, 4, 2, 5],), [1, 4, 4, 5]),
 (([0, -1, 0, 2],), [0, 0, 0, 2]),
 (([-3, -2, -1],), [-3, -2, -1]),
 (([5, 1, 7, 0, 9],), [5, 5, 7, 7, 9])]
