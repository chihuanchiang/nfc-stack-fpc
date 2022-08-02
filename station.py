import math
import pcbnew
from pcbnew import BOARD, FromMM, wxPoint
from typing import List

from coil import Coil, CoilStyle
from cuboid import Cuboid
from schematic import StationSchematic
import utils

class Station(Cuboid):

    def __init__(self, board: BOARD, sch: StationSchematic, coil_style: CoilStyle, length: int, height: int, stack_n: int):
        super().__init__(board, coil_style, length, height, stack_n)
        self._init_coils()
        self._init_footprints(sch)

    def _init_coils(self) -> None:
        l = self.length / (self.coil_n + 1)
        margin_b = max(self.coil_style.diameter / 2, FromMM(13)) + FromMM(2)
        margin_l = max(self.coil_style.diameter / 2, FromMM(12)) + FromMM(2)

        self.coil: List[Coil] = []
        for i in range(self.side):
            for j in range(self.coil_n):
                self.coil.append(Coil(self.board, self.coil_style, wxPoint(i * self.length + (j + 0.5) * l, -0.5 * l), math.radians(90), True))
        self.coil.append(Coil(self.board, self.coil_style, wxPoint(2 * self.length + margin_l, self.height - margin_b), 0))

    def _init_footprints(self, sch: StationSchematic) -> None:
        self.c_coil: List[pcbnew.FOOTPRINT]= [self.board.FindFootprintByReference(p.ref) for p in sch.c_coil]
        self.c_mux: pcbnew.FOOTPRINT = self.board.FindFootprintByReference(sch.c_mux.ref)
        self.mux: pcbnew.FOOTPRINT = self.board.FindFootprintByReference(sch.mux.ref)
        self.mcu: pcbnew.FOOTPRINT = self.board.FindFootprintByReference(sch.mcu.ref)
        self.head_ant: pcbnew.FOOTPRINT = self.board.FindFootprintByReference(sch.head_ant.ref)
        self.head_ftdi: pcbnew.FOOTPRINT = self.board.FindFootprintByReference(sch.head_ftdi.ref)

    def _layout_caps(self) -> None:
        for cap, co in zip(self.c_coil[:-1], self.coil[:-1]):
            t = co.get_terminal()
            cap.SetPosition(wxPoint((t[0].x + t[1].x) / 2, FromMM(3)))
        t = self.coil[-1].get_terminal()
        self.c_coil[-1].SetPosition(wxPoint(2 * self.length - FromMM(3), (t[0].y + t[1].y) / 2))
        self.c_coil[-1].SetOrientationDegrees(90)

    def _create_top(self, pos: wxPoint, angle: float) -> None:
        self._create_wing(pos, angle, self.coil_n)

    def _create_bottom(self, pos: wxPoint, angle: float) -> None:
        self._create_wing(pos, angle, 0) # No coils at the bottom

    def layout(self) -> None:
        self._layout_caps()
        
        self.head_ftdi.SetPosition(wxPoint(self.length / 2 + FromMM(4), self.height - FromMM(5)))
        self.head_ftdi.SetOrientationDegrees(-90)
        self.mcu.SetPosition(wxPoint(self.length / 2, self.head_ftdi.GetY() - FromMM(20)))
        self.mcu.SetOrientationDegrees(180)
        self.head_ant.SetPosition(wxPoint(self.length / 2 + FromMM(4), self.mcu.GetY() - FromMM(23)))
        self.head_ant.SetOrientationDegrees(-90)
        self.mux.SetPosition(wxPoint(1.5 * self.length, 0.5 * self.height))
        self.mux.SetOrientationDegrees(-90)
        self.c_mux.SetPosition(self.mux.GetPosition() + wxPoint(FromMM(8), 0))
        self.c_mux.SetOrientationDegrees(90)

    def create_coils(self) -> None:
        for cap, co in zip(self.c_coil, self.coil):
            co.create()
            co.extend(cap)

    def set_zones(self) -> None:
        clearance = FromMM(0.5)
        utils.add_zone(self.board, 0, self.length * self.side, -self.length, self.c_coil[0].GetPosition().y - clearance)
        utils.add_zone(self.board, 0, self.length * self.side, self.height, self.height + self.length)

        coil_ant = self.coil[-1]
        utils.add_zone(
            self.board,
            self.c_coil[-1].GetPosition().x + clearance,
            coil_ant.pos.x + coil_ant.diameter / 2 + clearance,
            coil_ant.pos.y - coil_ant.diameter / 2 - clearance,
            coil_ant.pos.y + coil_ant.diameter / 2 + clearance)