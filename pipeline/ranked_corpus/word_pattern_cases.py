TIER = "advanced"
TOPIC = "hash-maps"
FUNCTION = "word_pattern"
CASES = [
    (('abba', 'dog cat cat dog'), True),
    (('abba', 'dog cat cat fish'), False),
    (('aaaa', 'dog cat cat dog'), False),
    (('abba', 'dog dog dog dog'), False),
    (('abc', 'x y z'), True),
    (('ab', 'x y z'), False),
    (('a', 'x'), True),
    (('aba', 'x y x'), True),
]
