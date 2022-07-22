from pcbnew import *
from math import radians
from coil import Coil
from cuboid import Cuboid
from schematic import Schematic


class Station(Cuboid):

    def __init__(self, board: BOARD, coil: Coil, length: int, height: int, max_n: int, outline_width: int):
        super().__init__(board, coil, length, height, max_n, outline_width)


    def load_footprints(self, sch: Schematic) -> None:
        self.c_coil= [self.board.FindFootprintByReference(p.ref) for p in sch.c_coil]
        self.c_mux = self.board.FindFootprintByReference(sch.c_mux.ref)
        self.mux = self.board.FindFootprintByReference(sch.mux.ref)
        self.mcu = self.board.FindFootprintByReference(sch.mcu.ref)
        self.head_ant = self.board.FindFootprintByReference(sch.head_ant.ref)
        self.head_ftdi = self.board.FindFootprintByReference(sch.head_ftdi.ref)


    def layout(self) -> None:
        self.create_coils()
        
        self.head_ftdi.SetPosition(wxPoint(self.length / 2 + FromMM(4), self.height - FromMM(5)))
        self.head_ftdi.SetOrientationDegrees(-90)
        self.mcu.SetPosition(wxPoint(self.length / 2, self.head_ftdi.GetY() - FromMM(20)))
        self.mcu.SetOrientationDegrees(180)
        self.head_ant.SetPosition(wxPoint(self.length / 2 + FromMM(4), self.mcu.GetY() - FromMM(23)))
        self.head_ant.SetOrientationDegrees(-90)
        self.mux.SetPosition(wxPoint(1.5 * self.length, 0.5 * self.height))
        self.c_mux.SetPosition(self.mux.GetPosition() + wxPoint(FromMM(8), FromMM(-2)))
        self.c_mux.SetOrientationDegrees(-90)


    def create_coils(self) -> None:
        l = self.length / (self.coil_n + 1)
        terminal = []
        for i in range(self.side):
            for j in range(self.coil_n):
                terminal.append(self.coil.create(wxPoint(i * self.length + (j + 0.5) * l, -0.5 * l), radians(90), True))

        for c, t in zip(self.c_coil, terminal):
            c.SetPosition(wxPoint((t[0].x + t[1].x) / 2, FromMM(3)))

        reader_margin = {
            'bottom': max(self.coil.diameter / 2, FromMM(13)) + FromMM(2), 
            'left': max(self.coil.diameter / 2, FromMM(12)) + FromMM(2)}
        t = self.coil.create(wxPoint(2 * self.length + reader_margin['left'], self.height - reader_margin['bottom']), radians(180), True)
        self.c_coil[-1].SetPosition(wxPoint(2 * self.length - FromMM(3), (t[0].y + t[1].y) / 2))
        self.c_coil[-1].SetOrientationDegrees(90)


    def create_top(self, pos: wxPoint, angle: float) -> None:
        self.create_wing(pos, angle, self.coil_n)


    def create_bottom(self, pos: wxPoint, angle: float) -> None:
        self.create_wing(pos, angle, 0) # No coils at the bottom