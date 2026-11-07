TOPIC = 'sorting'
FUNCTION = 'selection_sort_copy'
EDITION = 'continuation-2026-11'
QUESTION_LIMIT = 5
DIFFICULTY_OFFSET = -50
PROMPT = 'Return a sorted copy using selection sort without changing the input list. Tap the buggy line.'
CASES = [(([],), []),
 (([1],), [1]),
 (([2, 1],), [1, 2]),
 (([1, 2],), [1, 2]),
 (([3, 1, 2],), [1, 2, 3]),
 (([3, 2, 1],), [1, 2, 3]),
 (([1, 1, 1],), [1, 1, 1]),
 (([2, 1, 2, 0],), [0, 1, 2, 2]),
 (([-3, 0, -1],), [-3, -1, 0]),
 (([-1, -2, -3],), [-3, -2, -1]),
 (([5, 2, 8, 1, 0],), [0, 1, 2, 5, 8]),
 (([0, 0, -1, 0],), [-1, 0, 0, 0])]
