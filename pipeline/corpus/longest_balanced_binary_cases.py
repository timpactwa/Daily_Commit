TOPIC = 'hash-maps'
FUNCTION = 'longest_balanced_binary'
EDITION = 'continuation-2026-11'
QUESTION_LIMIT = 5
DIFFICULTY_OFFSET = 250
PROMPT = 'Return the longest contiguous subarray length with equal zeros and ones; input contains only 0 and 1. Tap the buggy line.'
CASES = [(([],), 0),
 (([0],), 0),
 (([1],), 0),
 (([0, 1],), 2),
 (([1, 0],), 2),
 (([0, 0, 1],), 2),
 (([1, 1, 0, 0],), 4),
 (([0, 1, 0, 1, 1, 1, 0],), 4),
 (([0, 0, 0],), 0),
 (([1, 1, 1],), 0),
 (([0, 0, 1, 0, 1, 1],), 6),
 (([1, 0, 0, 0, 1],), 2),
 (([1, 1, 0, 1, 0, 0, 1, 0],), 8)]
