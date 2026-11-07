def gen_parens(n, current='', opened=0, closed=0):
    if len(current) == 2 * n:
        return [current]
    result = []
    if opened < n:
        result += gen_parens(n, current + '(', opened + 1, closed)
    if closed < opened:
        result += gen_parens(n, current + ')', opened, closed + 1)
    return result
