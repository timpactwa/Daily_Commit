TIER = "intermediate"
TOPIC = "recursion"
FUNCTION = "max_depth"
CASES = [
    (([],), 1),
    (([1, 2],), 1),
    (([1, [2]],), 2),
    (([[[3]]],), 3),
    (([1, [2, [3, [4]]], 5],), 4),
    (([[1], [2, [3]]],), 3),
]
