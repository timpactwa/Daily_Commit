TOPIC = 'recursion'
FUNCTION = 'balanced_parentheses'
EDITION = 'continuation-2026-11'
QUESTION_LIMIT = 5
DIFFICULTY_OFFSET = 175
PROMPT = 'For a string containing only ( and ), return whether it is balanced. Tap the buggy line.'
CASES = [(('',), True),
 (('(',), False),
 ((')',), False),
 (('()',), True),
 ((')(',), False),
 (('(())',), True),
 (('()()',), True),
 (('(()',), False),
 (('())(',), False),
 (('((()))',), True),
 (('(()())',), True),
 (('())',), False),
 (('(()(()))',), True)]
