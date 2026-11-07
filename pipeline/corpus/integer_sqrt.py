def integer_sqrt(number):
    lo = 0
    hi = number
    answer = 0
    while lo <= hi:
        mid = (lo + hi) // 2
        if mid * mid <= number:
            answer = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return answer
