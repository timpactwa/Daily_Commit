TOPIC = 'sorting'
FUNCTION = 'shell_sort'
EDITION = 'research-2026-11'
QUESTION_LIMIT = 4
DIFFICULTY_OFFSET = 125
PROMPT = 'Shell sort should return an ascending sorted copy for any integer list. Tap the buggy line.'
CASES = [(([],), []),
 (([2, 1],), [1, 2]),
 (([3, 1, 2],), [1, 2, 3]),
 (([5, 4, 3, 2, 1],), [1, 2, 3, 4, 5]),
 (([1, 2, 3],), [1, 2, 3]),
 (([4, 4, 1, 4],), [1, 4, 4, 4]),
 (([-3, 0, -1, 2],), [-3, -1, 0, 2]),
 (([0],), [0]),
 (([2, -2, 2, -2],), [-2, -2, 2, 2]),
 (([9, 2, 8, 1, 7, 0, 6, -1],), [-1, 0, 1, 2, 6, 7, 8, 9])]
