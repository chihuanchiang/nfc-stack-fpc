from pcbnew import *
from utils import *
from vector import *
from typing import Tuple


class Coil:

    def __init__(self, board: BOARD, top_layer: int, bottom_layer: int, diameter: int, track_w: int, track_s: int, n: int):
        self.board = board
        self.top_layer  = top_layer
        self.bottom_layer = bottom_layer
        self.diameter = diameter
        self.track_w = track_w
        self.track_s = track_s
        self.n = n
        self._set_points()


    def _set_points(self) -> None:
        self.start = wxPoint(-self.diameter / 2, -self.diameter / 2)
        self.end = self.start + wxPoint(-(self.track_w + self.track_s), self.track_w + self.track_s)
        curr = copy(self.start)
        length = self.diameter
        heading = [wxPoint(1, 0), wxPoint(0, 1), wxPoint(-1, 0), wxPoint(0, -1)]
        self.points = []
        self.points.append(curr)
        for i in range(self.n):
            for j in range(4):
                curr += multiplied(heading[j], length)
                self.points.append(copy(curr))
                if (j == 0 and i > 0) or (j == 2):
                    length -= self.track_w + self.track_s


    def create(self, pos: wxPoint, angle: float, flip: bool = False) -> Tuple[wxPoint, wxPoint]:
        func = flipped_x if flip else copy
        start = func(self.start)
        end = func(self.end)
        points = [func(p) for p in self.points]
        start = rotated(start, angle) + pos
        end = rotated(end, angle) + pos
        points = [rotated(p, angle) + pos for p in points]

        polyline(self.board, points, self.track_w, self.top_layer)
        segment(self.board, points[-1], end, self.track_w, self.bottom_layer)
        via(self.board, points[-1], self.track_w, (self.top_layer, self.bottom_layer))
        via(self.board, end, self.track_w, (self.top_layer, self.bottom_layer))
        return (start, end)