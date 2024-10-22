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
import vector

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
        self.head_ftdi.SetPosition(wxPoint(self.length / 2 + FromMM(4), self.height - FromMM(5)))
        self.head_ftdi.SetOrientationDegrees(-90)
        self.mcu.SetPosition(wxPoint(self.length / 2, self.head_ftdi.GetY() - FromMM(20)))
        self.mcu.SetOrientationDegrees(180)
        self.head_ant.SetPosition(wxPoint(self.length / 2 + FromMM(2), self.mcu.GetY() - FromMM(22)))
        self.head_ant.SetOrientationDegrees(-90)
        self.mux.SetPosition(wxPoint(1.5 * self.length, self.height - FromMM(25)))
        self.mux.SetOrientationDegrees(-90)

        for i in range(self.stack_n):
            t = self.coil[i].get_terminal()
            self.c_coil[i].SetPosition(wxPoint((t[0].x + t[1].x) / 2, FromMM(3)))
            if i >= self.stack_n / 2:
                self.c_coil[i].SetOrientationDegrees(180)
        t = self.coil[-1].get_terminal()
        self.c_coil[-1].SetPosition(wxPoint(self.mux.GetX() + FromMM(19), (t[0].y + t[1].y) / 2))
        self.c_coil[-1].SetOrientationDegrees(90)

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

    def _hf_cross(self, origin: wxPoint, traces: List[List[wxPoint]]) -> List[wxPoint]:
        cross = []
        for i in range(len(traces)):
            j = 0
            while j < len(traces[i]) - 1:
                p, state = vector.intersection(origin, origin + wxPoint(1, 0), traces[i][j], traces[i][j + 1])
                if state >= 2:
                    break
                p, state = vector.intersection(origin, origin + wxPoint(0, 1), traces[i][j], traces[i][j + 1])
                if state >= 2:
                    break
                j += 1
            cross.append(p)
            traces[i] = [p] + traces[i][j + 1:]

        utils.via(self.board, cross[0], self.coil_style.track_w, pcbnew.F_Cu, pcbnew.B_Cu)
        for i in range(len(cross) - 1):
            if cross[i].x == cross[i + 1].x or cross[i].y == cross[i + 1].y:
                utils.segment(self.board, cross[i], cross[i + 1], self.coil_style.track_w, pcbnew.B_Cu)
            else:
                utils.polyline(self.board, [cross[i], origin, cross[i + 1]], self.coil_style.track_w, pcbnew.B_Cu)
            utils.via(self.board, cross[i + 1], self.coil_style.track_w, pcbnew.F_Cu, pcbnew.B_Cu)

        return cross

    def _route(self) -> None:
        if AUTOROUTER:
            self._autoroute()
            return

        track_w = FromMM(0.4)
        track_clearance_x = FromMM(1)
        track_clearance_y = FromMM(1)
        pad_clearance = FromMM(0.4)
        hf_track_clearance_x = FromMM(2)
        hf_track_clearance_y = FromMM(4)
        hf_pad_clearance = FromMM(1)
        grid_size = FromMM(0.2)
        grid = path_finder.Grid(self.board, 0, self.length * self.side, self.c_coil[0].GetY(), self.height, grid_size)
        pads = self.board.GetPads()
        hf_pad = ["9", "8", "7", "6", "5", "4", "3", "2", "23", "22", "21", "20", "19", "18", "17", "16", "1"]
        mux_coil_pad = hf_pad[:-1]
        mux_ant_pad = hf_pad[-1]

        # ==================== Add walls to all pads ====================
        for pad in pads:
            if pad.GetParent().GetReference() == 'U1' and pad.GetName() in hf_pad:
                grid.add_wall_pad(pad, hf_pad_clearance)
            else:
                grid.add_wall_pad(pad, pad_clearance)

        # ==================== Route traces from the mux to capacitors ====================
        pads_mux_cap: List[Tuple[pcbnew.PAD, pcbnew.PAD]] = [(self.mux.FindPadByNumber(mux_coil_pad[i]), self.c_coil[i].Pads()[1]) for i in range(self.stack_n)]
        pads_mux_cap.sort(key=lambda e: abs(e[0].GetX() - e[1].GetX()), reverse=True)
        pads_mux_cap.append((self.mux.FindPadByNumber(mux_ant_pad), self.c_coil[-1].Pads()[0]))

        # Add a spacer to reserve space for the return path that will possibly pass by
        spacer_pos = self.head_ant.FindPadByNumber('1').GetPosition() + wxPoint(FromMM(2.5), 0)
        spacer_start = grid.pcb_to_grid(spacer_pos + wxPoint(0, FromMM(-4)))
        spacer_end = grid.pcb_to_grid(spacer_pos + wxPoint(0, FromMM(6)))
        grid.graph.add_wall_rect(spacer_start[0], spacer_end[0], spacer_start[1], spacer_end[1])

        traces_mux_cap = [grid.route_pad_to_pad(src_pad, dst_pad, self.coil_style.track_w, pcbnew.F_Cu, hf_pad_clearance, hf_track_clearance_x, hf_track_clearance_y)
                          for src_pad, dst_pad in pads_mux_cap]

        # Remove the spacer
        grid.graph.sub_wall_rect(spacer_start[0], spacer_end[0], spacer_start[1], spacer_end[1])

        # ==================== Route traces from the mcu to the ftdi header ====================
        pads_mcu_ftdi = [
            (self.mcu.FindPadByNumber('JP1_2'), self.head_ftdi.FindPadByNumber('4')),
            (self.mcu.FindPadByNumber('JP1_3'), self.head_ftdi.FindPadByNumber('3')),
            (self.mcu.FindPadByNumber('JP1_4'), self.head_ftdi.FindPadByNumber('2')),
            (self.mcu.FindPadByNumber('JP1_5'), self.head_ftdi.FindPadByNumber('1')),
            (self.mcu.FindPadByNumber('JP1_5'), self.mcu.FindPadByNumber('JP1_6')),
        ]
        traces_mcu_ftdi = [grid.route_pad_to_pad(src_pad, dst_pad, track_w, pcbnew.F_Cu, pad_clearance, track_clearance_x, track_clearance_y)
                           for src_pad, dst_pad in pads_mcu_ftdi]

        # ==================== Route traces from the antenna header to the mcu ====================
        pads_ant_mcu = [
            (self.head_ant.FindPadByNumber('3'), self.mcu.FindPadByNumber('JP2_1')),
            (self.head_ant.FindPadByNumber('4'), self.mcu.FindPadByNumber('JP2_2')),
            (self.head_ant.FindPadByNumber('2'), self.mcu.FindPadByNumber('JP1_4')),
            (self.head_ant.FindPadByNumber('1'), self.mcu.FindPadByNumber('JP1_5')),
        ]
        traces_ant_mcu = [grid.route_pad_to_pad(src_pad, dst_pad, track_w, pcbnew.F_Cu, pad_clearance, track_clearance_x, track_clearance_y)
                          for src_pad, dst_pad in pads_ant_mcu]

        # ==================== Route traces from the mux to the mcu ====================
        pads_mux_mcu = [
            (self.mux.FindPadByNumber('10'), self.mcu.FindPadByNumber('JP7_3')),
            (self.mux.FindPadByNumber('11'), self.mcu.FindPadByNumber('JP7_4')),
            (self.mux.FindPadByNumber('14'), self.mcu.FindPadByNumber('JP7_5')),
            (self.mux.FindPadByNumber('13'), self.mcu.FindPadByNumber('JP7_6')),
        ]

        # Add a spacer to route these traces below the mux
        spacer = [
            (
                grid.pcb_to_grid(self.mux.FindPadByNumber('10').GetPosition() + wxPoint(FromMM(-2), FromMM(2))),
                grid.pcb_to_grid(self.mux.FindPadByNumber('10').GetPosition() + wxPoint(FromMM(-2), FromMM(-2)))
            ),
            (
                grid.pcb_to_grid(self.mux.FindPadByNumber('10').GetPosition() + wxPoint(FromMM(-2), FromMM(-2))),
                grid.pcb_to_grid(self.mux.FindPadByNumber('13').GetPosition() + wxPoint(FromMM(2), FromMM(-2))),
            ),
        ]
        for s in spacer:
            grid.graph.add_wall_rect(s[0][0], s[1][0], s[0][1], s[1][1])

        traces_mux_mcu = [grid.route_pad_to_pad(src_pad, dst_pad, track_w, pcbnew.F_Cu, pad_clearance, track_clearance_x, track_clearance_y)
                          for src_pad, dst_pad in pads_mux_mcu]

        # Remove the spacer
        for s in spacer:
            grid.graph.sub_wall_rect(s[0][0], s[1][0], s[0][1], s[1][1])

        # ==================== Reset walls and add walls to all pads ====================
        grid.graph.reset_walls()
        for pad in pads:
            if pad.GetParent().GetReference() == 'U1' and pad.GetName() in hf_pad:
                grid.add_wall_pad(pad, hf_pad_clearance)
            else:
                grid.add_wall_pad(pad, pad_clearance)

        # ==================== Route VCC and GND from the ftdi header to the mux (bottom layer) ====================
        pads_ftdi_mux = [
            (self.head_ftdi.FindPadByNumber('1'), self.mux.FindPadByNumber('12')),
            (self.head_ftdi.FindPadByNumber('2'), self.mux.FindPadByNumber('24')),
        ]
        traces_ftdi_mux = [grid.route_pad_to_pad(src_pad, dst_pad, track_w, pcbnew.B_Cu, pad_clearance, track_clearance_x, track_clearance_y)
                          for src_pad, dst_pad in pads_ftdi_mux]

        # ==================== Route return paths from the capacitors ====================
        distance = FromMM(0.5) + self.coil_style.track_w

        traces_left = [t for t in traces_mux_cap[:-1] if t[-1].x < 2 * self.length]
        traces_right = [t for t in traces_mux_cap[:-1] if t[-1].x > 2 * self.length]
        traces_left.sort(key=lambda t: t[-1].x)
        traces_right.sort(key=lambda t: t[-1].x, reverse=True)

        caps_left = self.c_coil[:int(self.stack_n / 2)]
        caps_right = self.c_coil[-2:int(self.stack_n / 2) - 1:-1]

        traces_rtn_left = [vector.offset(path, -distance) for path in traces_left]
        traces_rtn_right = [vector.offset(path, distance) for path in traces_right]

        cross_left = self._hf_cross(self.mux.GetPosition() + wxPoint(FromMM(-21), FromMM(-9.5)), traces_rtn_left)
        cross_right = self._hf_cross(self.mux.GetPosition() + wxPoint(FromMM(21), 0), traces_rtn_right)

        for trace, cap in zip(traces_rtn_left, caps_left):
            trace[-1] = cap.Pads()[0].GetPosition()
            utils.polyline(self.board, trace, self.coil_style.track_w, pcbnew.F_Cu)
        for trace, cap in zip(traces_rtn_right, caps_right):
            trace[-1] = cap.Pads()[0].GetPosition()
            utils.polyline(self.board, trace, self.coil_style.track_w, pcbnew.F_Cu)

        utils.elbow(self.board, self.c_coil[-1].Pads()[1].GetPosition(), cross_left[0], self.coil_style.track_w, pcbnew.F_Cu)
        utils.elbow(self.board, cross_right[0], self.c_coil[-1].Pads()[1].GetPosition(), self.coil_style.track_w, pcbnew.F_Cu)

    def _create_coils(self) -> None:
        for cap, co in zip(self.c_coil, self.coil):
            co.create()
            co.extend(cap)

    def _create_markers(self) -> None:
        pass