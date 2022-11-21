import math
import pcbnew
from pcbnew import BOARD, wxPoint
from typing import Tuple

from eseries import find_nearest, E24
import utils
import vector

class CoilStyle:
    """Properties of a square NFC antenna"""

    def __init__(self, diameter: int, track_w: int, track_s: int, *, frequency: float = 13.56e6, q_factor: float = 100, turns: int = None):
        self.diameter = diameter
        self.track_w = track_w
        self.track_s = track_s
        self.freq = frequency
        self.q = q_factor
        
        self.diameter_M = 1e-9 * diameter
        self.track_w_M = 1e-9 * track_w
        self.track_s_M = 1e-9 * track_s

        if not turns:
            self.turns = self._get_optimal_turns()

        self.L = self._get_L()
        self.C = self._get_required_C()
        self.C_recommend = find_nearest(E24, self.C)

    def __repr__(self) -> str:
        return (
            f'  diameter: {self.diameter / 1e6} mm\n'
            f'  track_w: {self.track_w / 1e6} mm\n'
            f'  track_s: {self.track_s / 1e6} mm\n'
            f'  frequency: {self.freq / 1e6} MHz\n'
            f'  q_factor: {self.q}\n'
            f'  turns: {self.turns}\n'
            f'  C: {self.get_C_repr()}\n'
            f'  L: {self.get_L_repr()}'
        )

    def _get_inner_diameter(self, turns: int = None) -> float:
        """In meters"""
        if not turns:
            turns = self.turns
        return self.diameter_M - 2 * (turns * self.track_w_M + (turns - 1) * self.track_s_M)

    def _get_L(self, turns: int = None) -> float:
        """Returns the inductance of a square antenna"""
        if not turns:
            turns = self.turns
        do = self.diameter_M
        di = self._get_inner_diameter(turns)
        d = (do + di) / 2
        ratio = (do - di) / (do + di)
        k1, k2, mu = 2.34, 2.75, 4 * math.pi * 1e-7
        return k1 * mu * (turns ** 2) * (d / (1 + k2 * ratio))

    def _get_required_C(self) -> float:
        return 1 / (4 * math.pi * math.pi * (self.freq ** 2) * self._get_L())

    def _get_optimal_turns(self) -> int:
        max_turns = int(self.diameter_M / (self.track_w_M + self.track_s_M) / 2)
        prev_l = 0
        for curr_turns in range(1, max_turns + 1):
            curr_l = self._get_L(curr_turns)
            if (curr_l < prev_l):
                return curr_turns - 1
            prev_l = curr_l
        return max_turns

    def _get_repr(self, val: float) -> str:
        try:
            if val < 1e-9:
                # pico farad repr
                val *= 1e12
                return ('%.3g' % val) + 'p'
            if val < 1e-6:
                # nano farad repr
                val *= 1e9
                return ('%.3g' % val) + 'n'
            # micro farad repr
            val *= 1e6
            return ('%.3g' % val) + 'u'
        except NameError:
            return None

    def get_L_repr(self) -> str:
        return self._get_repr(self.L) + 'H'

    def get_C_repr(self) -> str:
        return self._get_repr(self.C) + 'F'

    def get_C_recommend_repr(self) -> str:
        return self._get_repr(self.C_recommend) + 'F'


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
        self._init_points()

    def _init_points(self) -> None:
        length = self.diameter - self.track_w
        self.start = wxPoint(-length / 2, -length / 2)
        self.end = self.start + wxPoint(-(self.track_w + self.track_s), self.track_w + self.track_s)
        curr = vector.copy(self.start)
        heading = [wxPoint(1, 0), wxPoint(0, 1), wxPoint(-1, 0), wxPoint(0, -1)]
        self.spiral = []
        self.spiral.append(curr)
        for i in range(self.turns):
            for j in range(4):
                curr += vector.multiplied(heading[j], length)
                self.spiral.append(vector.copy(curr))
                if (j == 0 and i > 0) or (j == 2):
                    length -= self.track_w + self.track_s

        self._translate(self.start)
        self._translate(self.end)
        for p in self.spiral:
            self._translate(p)

    def _translate(self, v: wxPoint) -> None:
        if self.flip:
            vector.flip_x(v)
        vector.rotate(v, self.angle)
        vector.add(v, self.pos)
        
    def create(self) -> None:
        utils.polyline(self.board, self.spiral, self.track_w, pcbnew.F_Cu)
        utils.segment(self.board, self.spiral[-1], self.end, self.track_w, pcbnew.B_Cu)
        utils.via(self.board, self.spiral[-1], self.track_w, pcbnew.F_Cu, pcbnew.B_Cu)
        utils.via(self.board, self.end, self.track_w, pcbnew.F_Cu, pcbnew.B_Cu)

    def get_terminal(self) -> Tuple[wxPoint, wxPoint]:
        return (vector.copy(self.start), vector.copy(self.end))

    def extend(self, cap: pcbnew.FOOTPRINT) -> None:
        pads = [p.GetPosition() for p in cap.Pads()]
        pairs = [
            [[self.start, pads[0]], [self.end, pads[1]]],
            [[self.start, pads[1]], [self.end, pads[0]]],
        ]
        loss = lambda pair: vector.dot_to_dot(pair[0][0], pair[0][1]) + vector.dot_to_dot(pair[1][0], pair[1][1])
        pair = pairs[0] if loss(pairs[0]) < loss(pairs[1]) else pairs[1]
        utils.segment(self.board, pair[0][0], pair[0][1], self.track_w, pcbnew.F_Cu)
        utils.segment(self.board, pair[1][0], pair[1][1], self.track_w, pcbnew.F_Cu)