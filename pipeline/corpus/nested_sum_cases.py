TOPIC = 'recursion'
FUNCTION = 'nested_sum'
EDITION = 'research-2026-11'
QUESTION_LIMIT = 3
DIFFICULTY_OFFSET = -25
PROMPT = 'Sum integers in arbitrarily nested lists; empty lists contribute 0. Tap the buggy line.'
CASES = [(([],), 0),
 (([1],), 1),
 (([1, [2, 3], 4],), 10),
 (([[[]]],), 0),
 (([-3, [2, -1]],), -2),
 (([[1], [2], [3]],), 6),
 (([0, [0, [5]]],), 5),
 (([[[[-2]]], 4],), 2)]
