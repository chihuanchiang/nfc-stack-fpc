import math
from pcbnew import wxPoint
from typing import List, Tuple

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
    if start == end:
        return dot_to_dot(p, start)

    v1 = p - start
    v2 = end - start
    pv = projection_value(v1, v2)
    if pv < 0:
        return dot_to_dot(p, start)
    if pv > mag(v2):
        return dot_to_dot(p, end)
    return dot_to_line(p, start, end)


def intersection(start1: wxPoint, end1: wxPoint, start2: wxPoint, end2: wxPoint) -> Tuple[wxPoint, int]:
    """Calculates the intersection of two line segments.

    Returns:
        A tuple containing the intersection point and the state of intersection.
        state:
            -2: invalid
            -1: parallel
            0: on none of the segments
            1: on segment 1
            2: on segment 2
            3: on both segments
    """
    if start1 == end1 or start2 == end2:
        return (wxPoint(0, 0), -2)

    v1 = end1 - start1
    v2 = end2 - start2
    v3 = start2 - start1
    divisor = v1.x * v2.y - v1.y * v2.x
    t_divident = v3.x * v2.y - v3.y * v2.x
    u_divident = v3.x * v1.y - v3.y * v1.x

    if divisor == 0:
        return (wxPoint(0, 0), -1)

    t = t_divident / divisor
    u = u_divident / divisor
    return (start1 + multiplied(v1, t), bool(0 <= t <= 1) + 2 * bool(0 <= u <= 1))


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


# ==================== Path Translations ====================
def offset(path: List[wxPoint], distance: int) -> List[wxPoint]:
    """Shifts `path` to the right by `distance`, and returns the shifted path."""
    segment = [[path[i], path[i + 1]] for i in range(len(path) - 1)]
    for s in segment:
        u = s[1] - s[0]
        rotate(u, math.radians(90))
        mult(u, distance / mag(u))
        s[0] += u
        s[1] += u

    shifted = [segment[0][0]]
    for i in range(len(segment) - 1):
        p, state = intersection(segment[i][0], segment[i][1], segment[i + 1][0], segment[i + 1][1])
        if state >= 0:
            shifted.append(p)
    shifted.append(segment[-1][1])
    return shifted