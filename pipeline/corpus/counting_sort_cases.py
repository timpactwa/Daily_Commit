TOPIC = 'sorting'
FUNCTION = 'counting_sort'
EDITION = 'research-2026-11'
QUESTION_LIMIT = 3
DIFFICULTY_OFFSET = 275
PROMPT = 'Counting sort must retain duplicates and handle negative integers in a small range. Tap the buggy line.'
CASES = [(([],), []),
 (([2, 1],), [1, 2]),
 (([3, 1, 2],), [1, 2, 3]),
 (([5, 4, 3, 2, 1],), [1, 2, 3, 4, 5]),
 (([1, 2, 3],), [1, 2, 3]),
 (([4, 4, 1, 4],), [1, 4, 4, 4]),
 (([-3, 0, -1, 2],), [-3, -1, 0, 2]),
 (([0],), [0]),
 (([2, -2, 2, -2],), [-2, -2, 2, 2]),
 (([-5, -5, -2],), [-5, -5, -2]),
 (([5, 5, 5],), [5, 5, 5])]
