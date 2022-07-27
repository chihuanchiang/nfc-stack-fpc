from pcbnew import *
from utils import *
from vector import *
from typing import Tuple
from math import hypot


class CoilStyle:

    def __init__(self, diameter: int, track_w: int, track_s: int, turns: int):
        self.diameter = diameter
        self.track_w = track_w
        self.track_s = track_s
        self.turns = turns


class Coil:

    def __init__(self, board: BOARD, style: CoilStyle, pos: wxPoint, angle: float, flip: bool = False):
        self.board = board
        self.diameter = style.diameter
        self.track_w = style.track_w
        self.track_s = style.track_s
        self.turns = style.turns
        self.pos = pos
        self.angle = angle
        self.flip = flip
        self._set_points()


    def _set_points(self) -> None:
        self.start = wxPoint(-self.diameter / 2, -self.diameter / 2)
        self.end = self.start + wxPoint(-(self.track_w + self.track_s), self.track_w + self.track_s)
        curr = copy(self.start)
        length = self.diameter - self.track_w
        heading = [wxPoint(1, 0), wxPoint(0, 1), wxPoint(-1, 0), wxPoint(0, -1)]
        self.spiral = []
        self.spiral.append(curr)
        for i in range(self.turns):
            for j in range(4):
                curr += multiplied(heading[j], length)
                self.spiral.append(copy(curr))
                if (j == 0 and i > 0) or (j == 2):
                    length -= self.track_w + self.track_s

        self._translate(self.start)
        self._translate(self.end)
        for p in self.spiral:
            self._translate(p)


    def _translate(self, v: wxPoint) -> None:
        if self.flip:
            flip_x(v)
        rotate(v, self.angle)
        add(v, self.pos)
        

    def create(self) -> None:
        polyline(self.board, self.spiral, self.track_w, F_Cu)
        segment(self.board, self.spiral[-1], self.end, self.track_w, B_Cu)
        via(self.board, self.spiral[-1], self.track_w, F_Cu, B_Cu)
        via(self.board, self.end, self.track_w, F_Cu, B_Cu)


    def get_terminal(self) -> Tuple[wxPoint, wxPoint]:
        return (copy(self.start), copy(self.end))


    def extend(self, cap: FOOTPRINT) -> None:

        def _loss(pair) -> float:
            v1 = pair[0][0] - pair[0][1]
            v2 = pair[1][0] - pair[1][1]
            return hypot(v1.x, v1.y) + hypot(v2.x, v2.y)

        pads = [p.GetPosition() for p in cap.Pads()]
        pairs = [
            [[self.start, pads[0]], [self.end, pads[1]]],
            [[self.start, pads[1]], [self.end, pads[0]]],
        ]
        pair = pairs[0] if _loss(pairs[0]) < _loss(pairs[1]) else pairs[1]
        segment(self.board, pair[0][0], pair[0][1], self.track_w, F_Cu)
        segment(self.board, pair[1][0], pair[1][1], self.track_w, F_Cu)