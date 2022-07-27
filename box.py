from pcbnew import *
from utils import *
from vector import *
from coil import Coil, CoilStyle
from cuboid import Cuboid

class Box(Cuboid):

    def __init__(self, board: BOARD, coil_style: CoilStyle, length: int, stack_n: int):
        super().__init__(board, coil_style, length, length, stack_n)


    def create_top(self, pos: wxPoint, angle: float) -> None:
        self.create_wing(pos, angle, ceil(self.stack_n / self.side))


    def create_bottom(self, pos: wxPoint, angle: float) -> None:
        self.create_top(pos, angle)