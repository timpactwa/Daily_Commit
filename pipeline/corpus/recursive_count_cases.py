TOPIC = 'recursion'
FUNCTION = 'recursive_count'
EDITION = 'continuation-2026-11'
QUESTION_LIMIT = 5
DIFFICULTY_OFFSET = 25
PROMPT = 'Recursively count target occurrences in an integer list; the list need not be sorted. Tap the buggy line.'
CASES = [(([], 0), 0),
 (([1], 1), 1),
 (([1], 0), 0),
 (([2, 1, 2, 2], 2), 3),
 (([0, 0, 0], 0), 3),
 (([-1, 2, -1, 0], -1), 2),
 (([1, 2, 3, 4], 5), 0),
 (([4, 3, 2, 1], 1), 1),
 (([7, 7, 1, 7, 2, 7], 7), 4),
 (([0, -1, 2], 2), 1),
 (([1, 2], 1), 1)]
