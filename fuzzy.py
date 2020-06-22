from collections import namedtuple

class TriangleFunction:
    M = 256

    def __init__(self, x1, x3):
        if x1 > x3:
            temp = x3
            x3 = x1
            x1 = temp
        self.x1 = x1
        self.x2 = (x1 + x3) // 2
        self.x3 = x3
        self.k1_denominator = max(1, self.x2 - x1)
        self.k2_denominator = min(-1, self.x2 - x3)

    def __call__(self, x):
        if x <= self.x1 or x >= self.x3:
            return 0
        if x <= self.x2:
            return self.M * (x - self.x1) // self.k1_denominator
        else:
            return self.M * (x - self.x3) // self.k2_denominator

_5Levels = namedtuple('FiveLevels', ('NM', 'NS', 'Z', 'PS', 'PM'))
_3Levels = namedtuple('ThreeLevels', ('NM', 'Z', 'PM'))
_3LevelsPositive = namedtuple('ThreeLevelsPositive', ('Z', 'PS', 'PM'))

def FiveLevels(NM, NS, Z, PS, PM):
    return _5Levels(
        TriangleFunction(*NM),
        TriangleFunction(*NS),
        TriangleFunction(*Z),
        TriangleFunction(*PS),
        TriangleFunction(*PM)
    )

def ThreeLevels(NM, Z, PM):
    return _3Levels(
        TriangleFunction(*NM),
        TriangleFunction(*Z),
        TriangleFunction(*PM)
    )

def ThreeLevelsPositive(Z, PS, PM):
    return _3LevelsPositive(
        TriangleFunction(*Z),
        TriangleFunction(*PS),
        TriangleFunction(*PM)
    )

class Defuzzer:
    def __init__(self):
        self.numerator = 0
        self.denominator = 0

    def feed(self, y2, output):
        self.numerator += y2 * output
        self.denominator += output

    def defuzz(self):
        return self.numerator // max(1, self.denominator)

    def reset(self):
        self.__init__()
