from pcbnew import *
from utils import *
from vector import *
from coil import Coil
from cuboid import Cuboid

class Box(Cuboid):

    def __init__(self, board: BOARD, coil: Coil, length: int, max_n: int, outline_width: int):
        super().__init__(board, coil, length, length, max_n, outline_width)


    def create_top(self, pos: wxPoint, angle: float) -> None:
        self.create_wing(pos, angle, ceil(self.max_n / self.side))


    def create_bottom(self, pos: wxPoint, angle: float) -> None:
        self.create_top(pos, angle)