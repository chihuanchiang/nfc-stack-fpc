import math
import pcbnew
from pcbnew import BOARD, FromMM, wxPoint
from typing import List

from coil import Coil, CoilStyle
from cuboid import Cuboid
from schematic import BoxSchematic
import utils

class Box(Cuboid):

    def __init__(self, board: BOARD, sch: BoxSchematic, coil_style: CoilStyle, length: int, stack_n: int):
        super().__init__(board, coil_style, length, length, stack_n)
        self._init_coils()
        self._init_footprints(sch)
        self.tag_d = FromMM(10)

    def _init_coils(self) -> None:
        l = self.length / (self.coil_n + 1)

        self.coil_top: List[Coil] = []
        self.coil_bottom: List[Coil] = []
        for i in range(self.side):
            for j in range(self.coil_n):
                if not ((i == self.side - 1 ) and (j == self.coil_n - 1)):
                    self.coil_top.append(Coil(self.board, self.coil_style, wxPoint(i * self.length + (j + 0.5) * l, -0.5 * l), math.radians(90), True))
                    self.coil_bottom.append(Coil(self.board, self.coil_style, wxPoint(i * self.length + (j + 1.5) * l, 0.5 * l + self.height), math.radians(90)))

    def _init_footprints(self, sch: BoxSchematic) -> None:
        self.c_coil_top: List[pcbnew.FOOTPRINT] = [self.board.FindFootprintByReference(p.ref) for p in sch.c_coil_top]
        self.c_coil_bottom: List[pcbnew.FOOTPRINT] = [self.board.FindFootprintByReference(p.ref) for p in sch.c_coil_bottom]

    def _layout_caps(self) -> None:
        offset = FromMM(3)
        for cap, co in zip(self.c_coil_top, self.coil_top):
            t = co.get_terminal()
            cap.SetPosition(wxPoint((t[0].x + t[1].x) / 2, offset))
        for cap, co in zip(self.c_coil_bottom, self.coil_bottom):
            t = co.get_terminal()
            cap.SetPosition(wxPoint((t[0].x + t[1].x) / 2, self.height - offset))

    def _create_top(self, pos: wxPoint, angle: float) -> None:
        self._create_wing(pos, angle, self.coil_n)

    def _create_bottom(self, pos: wxPoint, angle: float) -> None:
        self._create_top(pos, angle)

    def create_tag_marker(self) -> None:
        l = self.length / (self.coil_n + 1) / 2
        utils.circle(self.board, wxPoint(self.side * self.length - l, self.height + l), self.tag_d, self.outline_width, self.board.GetLayerID('B.Silkscreen'), False)

    def layout(self) -> None:
        self._layout_caps()

    def create_coils(self) -> None:
        for cap, co in zip(self.c_coil_top, self.coil_top):
            co.create()
            co.extend(cap)
        for cap, co in zip(self.c_coil_bottom, self.coil_bottom):
            co.create()
            co.extend(cap)

    def route_caps(self) -> None:
        for ct, cb in zip(self.c_coil_top, self.c_coil_bottom):
            utils.segment(self.board, ct.Pads()[0].GetPosition(), cb.Pads()[0].GetPosition(), self.coil_style.track_w, pcbnew.F_Cu)
            utils.segment(self.board, ct.Pads()[1].GetPosition(), cb.Pads()[1].GetPosition(), self.coil_style.track_w, pcbnew.F_Cu)