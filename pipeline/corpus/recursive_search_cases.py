TOPIC = 'recursion'
FUNCTION = 'recursive_search'
EDITION = 'research-2026-11'
QUESTION_LIMIT = 3
DIFFICULTY_OFFSET = 275
PROMPT = 'Recursively search sorted distinct values between inclusive lo and hi. An empty interval returns -1. Tap the buggy line.'
CASES = [(([], 3, 0, -1), -1),
 (([1], 1, 0, 0), 0),
 (([1], 2, 0, 0), -1),
 (([1, 3, 5, 7], 7, 0, 3), 3),
 (([1, 3, 5, 7], 1, 0, 3), 0),
 (([1, 3, 5, 7], 3, 1, 2), 1),
 (([1, 3, 5, 7], 1, 1, 3), -1),
 (([2, 4, 6], 5, 0, 2), -1)]
