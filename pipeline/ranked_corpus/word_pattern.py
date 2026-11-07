def word_pattern(pattern, text):
    words = text.split()
    if len(words) != len(pattern):
        return False
    to_word = {}
    to_char = {}
    for ch, word in zip(pattern, words):
        if ch in to_word and to_word[ch] != word:
            return False
        if word in to_char and to_char[word] != ch:
            return False
        to_word[ch] = word
        to_char[word] = ch
    return True
