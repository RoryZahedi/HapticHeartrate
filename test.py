num = 7
match age:
    case num if num in range(1, 26):
        ageRange = 0
        break
    case num if num in range(26, 36):
        ageRange = 1
        break
    case num if num in range(36, 46):
        ageRange = 2
        break
    case num if num in range(46, 56):
        ageRange = 3
        break
    case num if num in range(56, 66):
        ageRange = 4
        break
    case _:
        ageRange = 5
        break