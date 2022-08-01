import math
from pcbnew import wxPoint

# ==================== Arithmetic Operators ====================
def copy(v: wxPoint) -> wxPoint:
    return wxPoint(v.x, v.y)


def add(u: wxPoint, v: wxPoint) -> None:
    u.x += v.x
    u.y += v.y


def sub(u: wxPoint, v: wxPoint) -> None:
    u.x -= v.x
    u.y -= v.y


def mult(v: wxPoint, n: float) -> None:
    v.x = int(v.x * n)
    v.y = int(v.y * n)


def multiplied(v: wxPoint, n: float) -> wxPoint:
    return wxPoint(v.x * n, v.y * n)


def div(v: wxPoint, n: float) -> None:
    v.x = int(v.x / n)
    v.y = int(v.y / n)


def divided(v: wxPoint, n: float) -> wxPoint:
    return wxPoint(v.x / n, v.y / n)


# ==================== Vector Operators ====================
def mag(v: wxPoint) -> float:
    return math.hypot(v.x, v.y)


def inner_prod(u: wxPoint, v: wxPoint) -> int:
    return u.x * v.x + u.y * v.y


def cross_prod(u: wxPoint, v: wxPoint) -> int:
    return u.x * v.y - u.y * v.x


def projection_value(u: wxPoint, v: wxPoint) -> float:
    """returns the value of u's projection onto v. v can not be a zero vector"""
    return inner_prod(u, v) / mag(v)


# ==================== Geometry ====================
def dot_to_dot(u: wxPoint, v: wxPoint) -> float:
    return mag(u - v)


def dot_to_line(p: wxPoint, start: wxPoint, end: wxPoint) -> float:
    """start and end can not be the same point"""
    v1 = p - start
    v2 = end - start
    return abs(cross_prod(v1, v2)) / mag(v2)


def dot_to_segment(p: wxPoint, start: wxPoint, end: wxPoint) -> float:
    """The segment is treated as a dot if start and end are the same point"""
    v1 = p - start
    v2 = end - start
    if v2 == wxPoint(0, 0):
        return dot_to_dot(p, start)

    pv = projection_value(v1, v2)
    if pv < 0:
        return dot_to_dot(p, start)
    if pv > mag(v2):
        return dot_to_dot(p, end)
    return dot_to_line(p, start, end)


# ==================== Translations ====================
def rotate(v: wxPoint, angle: float, center: wxPoint = wxPoint(0, 0)) -> None:
    sub(v, center)
    new_x = v.x * math.cos(angle) - v.y * math.sin(angle)
    new_y = v.x * math.sin(angle) + v.y * math.cos(angle)
    v.x = int(new_x)
    v.y = int(new_y)
    add(v, center)
    

def rotated(v: wxPoint, angle: float, center: wxPoint = wxPoint(0, 0)) -> wxPoint:
    new_v = copy(v)
    rotate(new_v, angle, center)
    return new_v


def flip_x(v: wxPoint, center: wxPoint = wxPoint(0, 0)) -> None:
    v.x = 2 * center.x - v.x


def flipped_x(v: wxPoint, center: wxPoint = wxPoint(0, 0)) -> wxPoint:
    return wxPoint(2 * center.x - v.x, v.y)


def flip_y(v: wxPoint, center: wxPoint = wxPoint(0, 0)) -> None:
    v.y = 2 * center.y - v.y


def flipped_y(v: wxPoint, center: wxPoint = wxPoint(0, 0)) -> wxPoint:
    return wxPoint(v.x, 2 * center.y - v.y)