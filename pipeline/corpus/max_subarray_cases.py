TOPIC = 'arrays-strings'
FUNCTION = 'max_subarray'
EDITION = 'research-2026-11'
QUESTION_LIMIT = 4
DIFFICULTY_OFFSET = 150
PROMPT = 'Find the largest nonempty contiguous-subarray sum; return 0 for empty input. Tap the buggy line.'
CASES = [(([],), 0),
 (([-8],), -8),
 (([-4, -2, -7],), -2),
 (([4, -1, 2, 1],), 6),
 (([-2, 1, -3, 4, -1, 2, 1, -5, 4],), 6),
 (([1, 2, 3],), 6),
 (([0, 0],), 0),
 (([8, -10, 5],), 8)]
