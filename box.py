import math
from pcbnew import BOARD, wxPoint

from coil import Coil, CoilStyle
from cuboid import Cuboid

class Box(Cuboid):

    def __init__(self, board: BOARD, coil_style: CoilStyle, length: int, stack_n: int):
        super().__init__(board, coil_style, length, length, stack_n)

    def _create_top(self, pos: wxPoint, angle: float) -> None:
        self._create_wing(pos, angle, math.ceil(self.stack_n / self.side))

    def _create_bottom(self, pos: wxPoint, angle: float) -> None:
        self._create_top(pos, angle)