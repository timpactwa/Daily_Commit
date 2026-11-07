def balanced_parentheses(text):

    def walk(index, depth):
        if depth < 0:
            return False
        if index == len(text):
            return depth == 0
        if text[index] == '(':
            return walk(index + 1, depth + 1)
        return walk(index + 1, depth - 1)
    return walk(0, 0)
