import math
import os
import pcbnew
from pcbnew import BOARD, FromMM, wxPoint
from typing import List, Tuple

from coil import Coil, CoilStyle
from cuboid import Cuboid
import path_finder
from schematic import StationSchematic
import utils

AUTOROUTER = False

class Station(Cuboid):

    def __init__(self, board: BOARD, sch: StationSchematic, coil_style: CoilStyle, length: int, height: int, stack_n: int):
        super().__init__(board, sch, coil_style, length, height, stack_n)

    def _init_coils(self) -> None:
        l = self.length / (self.coil_n + 1)
        margin_b = max(self.coil_style.diameter / 2, FromMM(13)) + FromMM(2)
        margin_l = max(self.coil_style.diameter / 2, FromMM(12)) + FromMM(10)

        self.coil: List[Coil] = []
        for i in range(self.side):
            for j in range(self.coil_n):
                self.coil.append(Coil(self.board, self.coil_style, wxPoint(i * self.length + (j + 0.5) * l, -0.5 * l), math.radians(90), True))
        self.coil.append(Coil(self.board, self.coil_style, wxPoint(2 * self.length + margin_l, self.height - margin_b), 0))

    def _init_footprints(self) -> None:
        self.c_coil: List[pcbnew.FOOTPRINT]= [self.board.FindFootprintByReference(p.ref) for p in self.sch.c_coil]
        self.mux: pcbnew.FOOTPRINT = self.board.FindFootprintByReference(self.sch.mux.ref)
        self.mcu: pcbnew.FOOTPRINT = self.board.FindFootprintByReference(self.sch.mcu.ref)
        self.head_ant: pcbnew.FOOTPRINT = self.board.FindFootprintByReference(self.sch.head_ant.ref)
        self.head_ftdi: pcbnew.FOOTPRINT = self.board.FindFootprintByReference(self.sch.head_ftdi.ref)

    def _create_top(self, pos: wxPoint, angle: float) -> None:
        self._create_wing(pos, angle, self.coil_n)

    def _create_bottom(self, pos: wxPoint, angle: float) -> None:
        self._create_wing(pos, angle, 0) # No coils at the bottom

    def _layout(self) -> None:
        for i in range(self.stack_n):
            t = self.coil[i].get_terminal()
            self.c_coil[i].SetPosition(wxPoint((t[0].x + t[1].x) / 2, FromMM(3)))
            if i >= self.stack_n / 2:
                self.c_coil[i].SetOrientationDegrees(180)
        t = self.coil[-1].get_terminal()
        self.c_coil[-1].SetPosition(wxPoint(2 * self.length - FromMM(3), (t[0].y + t[1].y) / 2))
        self.c_coil[-1].SetOrientationDegrees(90)
        
        self.head_ftdi.SetPosition(wxPoint(self.length / 2 + FromMM(4), self.height - FromMM(5)))
        self.head_ftdi.SetOrientationDegrees(-90)
        self.mcu.SetPosition(wxPoint(self.length / 2, self.head_ftdi.GetY() - FromMM(20)))
        self.mcu.SetOrientationDegrees(180)
        self.head_ant.SetPosition(wxPoint(self.length / 2 + FromMM(2), self.mcu.GetY() - FromMM(22)))
        self.head_ant.SetOrientationDegrees(-90)
        self.mux.SetPosition(wxPoint(1.5 * self.length, self.height - FromMM(25)))
        self.mux.SetOrientationDegrees(-90)

    def _autoroute(self) -> None:
        # Set keepout zones
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

        # Call third-party router
        project_name = os.path.splitext(self.board.GetFileName())[0]
        utils.route(self.board, project_name)
        self._update_board()

    def _route(self) -> None:
        if AUTOROUTER:
            self._autoroute()
            return

        grid_size = FromMM(0.2)
        grid = path_finder.Grid(0, self.length * self.side, self.c_coil[0].GetY(), self.height, grid_size)
        pads = self.board.GetPads()
        tracks = [t for t in self.board.Tracks() if type(t) == pcbnew.PCB_TRACK]
        vias = [v for v in self.board.Tracks() if type(v) == pcbnew.PCB_VIA]
        mux_coil_pin = [9, 8, 7, 6, 5, 4, 3, 2, 23, 22, 21, 20, 19, 18, 17, 16]
        mux_coil_pin = ["9", "8", "7", "6", "5", "4", "3", "2", "23", "22", "21", "20", "19", "18", "17", "16"]
        mux_ant_pin = "1"

        # ==================== Add walls to all pads ====================
        grid.graph.reset_walls()
        pad_clearance = FromMM(1)
        for pad in pads:
            grid.add_wall_pad(pad, pad_clearance)
        # Reserve space for the return path that will possibly pass by
        grid.add_wall_pad(self.head_ant.FindPadByNumber('1'), FromMM(3))

        # ==================== Route traces from the mux to capacitors ====================
        pads_mux_cap: List[Tuple[pcbnew.PAD, pcbnew.PAD]] = [(self.mux.FindPadByNumber(mux_coil_pin[i]), self.c_coil[i].Pads()[1]) for i in range(self.stack_n)]
        pads_mux_cap.sort(key=lambda e: abs(e[0].GetX() - e[1].GetX()), reverse=True)
        pads_mux_cap.append((self.mux.FindPadByNumber(mux_ant_pin), self.c_coil[-1].Pads()[0]))

        for src_pad, dst_pad in pads_mux_cap:
            grid.graph.reset_nodes()
            print(f"{src_pad.GetName()} -> {dst_pad.GetName()}")
            src_pos = src_pad.GetPosition()
            dst_pos = dst_pad.GetPosition()
            src = grid.get_node(src_pos)
            dst = grid.get_node(dst_pos)

            grid.sub_wall_pad(src_pad, pad_clearance)
            grid.sub_wall_pad(dst_pad, pad_clearance)
            path = path_finder.find_path(grid.graph, src, dst)
            grid.add_wall_pad(src_pad, pad_clearance)
            grid.add_wall_pad(dst_pad, pad_clearance)

            grid.add_wall_path(path, FromMM(2), FromMM(4))

            vertices = path_finder.get_vertices(path)
            point = [grid.grid_to_pcb(p.x, p.y) for p in vertices]
            point[0], point[-1] = src_pos, dst_pos
            utils.polyline(self.board, point, self.coil_style.track_w, pcbnew.F_Cu)

    def _create_coils(self) -> None:
        for cap, co in zip(self.c_coil, self.coil):
            co.create()
            co.extend(cap)

    def _create_markers(self) -> None:
        pass