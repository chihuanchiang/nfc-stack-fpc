from abc import ABC, abstractmethod
import math
import pcbnew
from pcbnew import FromMM, wxPoint, BOARD

from coil import CoilStyle
from schematic import Schematic
import utils
import vector

class Cuboid(ABC):

    def __init__(self, board: BOARD, sch: Schematic, coil_style: CoilStyle, length: int, height: int, stack_n: int):
        self.board = board
        self.sch = sch
        self.coil_style = coil_style
        self.length = length
        self.height = height
        self.stack_n = stack_n
        self.outline_width = FromMM(0.2)
        self.side = 4
        self.coil_n = math.ceil(stack_n / self.side)
        self._init_coils()
        self._init_footprints()

    def _update_board(self) -> None:
        self.board = pcbnew.LoadBoard(self.board.GetFileName())
        self._init_coils()
        self._init_footprints()

    def _create_tab(self, width: int = FromMM(4), taper_angle: float = math.radians(15)) -> None:
        offset = width * math.tan(taper_angle)
        points = [
            wxPoint(0, 0),
            wxPoint(-width, offset),
            wxPoint(-width, self.height - offset),
            wxPoint(0, self.height),
        ]
        utils.polyline(self.board, points, self.outline_width, pcbnew.Edge_Cuts, False)

    def _create_wing(self, pos: wxPoint, angle: float, coil_n: int) -> None:
        tolerance = FromMM(0.8)
        parts = (coil_n + 1) if (coil_n > 0) else 2
        l = self.length / parts
        h = l * (parts - 2) / 2

        points = [wxPoint(self.length, 0), wxPoint(self.length, l)]
        if h > tolerance:
            points.append(wxPoint(self.length - l - tolerance, l))
            points.append(wxPoint(self.length - l - tolerance, l + h))
            points.append(wxPoint(l + h, l + h))
        points.append(wxPoint(l, l))
        points.append(wxPoint(0, 0))

        for p in points:
            vector.rotate(p, angle)
            vector.add(p, pos)
        utils.polyline(self.board, points, self.outline_width, pcbnew.Edge_Cuts, False)

        points = [
            wxPoint(l, l / 3 + tolerance),
            wxPoint(l, l / 3),
            wxPoint(l * 2 / 3, 0),
            wxPoint(l * 2 / 3 - tolerance, 0),
        ]

        for p in points:
            vector.rotate(p, angle)
            vector.add(p, pos)
        utils.polyline(self.board, points, self.outline_width, pcbnew.Edge_Cuts, False)

    def _create_outline(self) -> None:
        self._create_tab()
        utils.segment(
            self.board, 
            wxPoint(self.side * self.length, 0), 
            wxPoint(self.side * self.length, self.height), 
            self.outline_width, 
            pcbnew.Edge_Cuts, 
            False,
        )

        for i in range(self.side):
            self._create_top(wxPoint((i + 1) * self.length, 0), math.radians(180))
            self._create_bottom(wxPoint(i * self.length, self.height), 0)

    def _create_foldline(self) -> None:
        diameter = FromMM(0.6)
        distance = FromMM(1)
        clearance = FromMM(0.075)
        utils.fold_line(self.board, wxPoint(0, 0), wxPoint(self.side * self.length, 0), diameter, distance, self.outline_width, clearance)
        utils.fold_line(self.board, wxPoint(0, self.height), wxPoint(self.side * self.length, self.height), diameter, distance, self.outline_width, clearance)
        for i in range(self.side):
            utils.fold_line(self.board, wxPoint(i * self.length, 0), wxPoint(i * self.length, self.height), diameter, distance, self.outline_width, clearance)

    @abstractmethod
    def _init_coils(self) -> None:
        pass

    @abstractmethod
    def _init_footprints(self) -> None:
        pass

    @abstractmethod
    def _create_top(self, pos: wxPoint, angle: float) -> None:
        pass

    @abstractmethod
    def _create_bottom(self, pos: wxPoint, angle: float) -> None:
        pass

    @abstractmethod
    def _layout(self) -> None:
        pass

    @abstractmethod
    def _route(self) -> None:
        pass

    @abstractmethod
    def _create_coils(self) -> None:
        pass

    @abstractmethod
    def _create_markers(self) -> None:
        pass

    def create(self) -> BOARD:
        self._layout()
        self._route()
        self._create_outline()
        self._create_coils()
        self._create_foldline()
        self._create_markers()
        return self.board