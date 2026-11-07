TOPIC = 'hash-maps'
FUNCTION = 'longest_consecutive'
EDITION = 'research-2026-11'
QUESTION_LIMIT = 4
DIFFICULTY_OFFSET = 125
PROMPT = 'Find the longest run of consecutive integer values, ignoring input order and duplicates. Tap the buggy line.'
CASES = [(([],), 0),
 (([1],), 1),
 (([100, 4, 200, 1, 3, 2],), 4),
 (([1, 2, 0, 1],), 3),
 (([-2, -1, 0, 5],), 3),
 (([9, 7, 5],), 1),
 (([4, 3, 2, 1],), 4),
 (([10, 11, 12, 2, 3],), 3),
 (([0, 0, 0],), 1)]
