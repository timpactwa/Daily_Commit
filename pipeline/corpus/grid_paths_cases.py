TOPIC = 'recursion'
FUNCTION = 'grid_paths'
EDITION = 'research-2026-11'
QUESTION_LIMIT = 4
DIFFICULTY_OFFSET = 150
PROMPT = 'Count top-left to bottom-right grid paths using only right/down moves. Nonpositive dimensions have 0 paths. Tap the buggy line.'
CASES = [((0, 0), 0),
 ((0, 3), 0),
 ((3, 0), 0),
 ((-1, 2), 0),
 ((1, 1), 1),
 ((1, 5), 1),
 ((5, 1), 1),
 ((2, 2), 2),
 ((3, 4), 10),
 ((4, 4), 20)]
