from pcbnew import *
from math import sin, cos


def copy(v: wxPoint) -> wxPoint:
    return wxPoint(v.x, v.y)


def add(v: wxPoint, u: wxPoint) -> None:
    v.x += u.x
    v.y += u.y


def sub(v: wxPoint, u: wxPoint) -> None:
    v.x -= u.x
    v.y -= u.y


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


def rotate(v: wxPoint, angle: float, center: wxPoint = wxPoint(0, 0)) -> None:
    sub(v, center)
    new_x = v.x * cos(angle) - v.y * sin(angle)
    new_y = v.x * sin(angle) + v.y * cos(angle)
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