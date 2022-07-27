from pcbnew import *
from utils import *
from vector import *
from math import radians, tan, ceil
from abc import ABC, abstractmethod
from coil import CoilStyle


class Cuboid(ABC):

    def __init__(self, board: BOARD, coil_style: CoilStyle, length: int, height: int, stack_n: int):
        self.board = board
        self.coil_style = coil_style
        self.length = length
        self.height = height
        self.stack_n = stack_n
        self.outline_width = FromMM(0.1)
        self.side = 4
        self.coil_n = ceil(stack_n / self.side)


    def create_tab(self, width: int = FromMM(4), taper_angle: float = radians(15)) -> None:
        offset = width * tan(taper_angle)
        points = [
            wxPoint(0, 0),
            wxPoint(-width, offset),
            wxPoint(-width, self.height - offset),
            wxPoint(0, self.height),
        ]
        polyline(self.board, points, self.outline_width, Edge_Cuts, False)


    def create_wing(self, pos: wxPoint, angle: float, coil_n: int) -> None:
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
            rotate(p, angle)
            add(p, pos)
        polyline(self.board, points, self.outline_width, Edge_Cuts, False)

        points = [
            wxPoint(l, l / 3 + tolerance),
            wxPoint(l, l / 3),
            wxPoint(l * 2 / 3, 0),
            wxPoint(l * 2 / 3 - tolerance, 0),
        ]

        for p in points:
            rotate(p, angle)
            add(p, pos)
        polyline(self.board, points, self.outline_width, Edge_Cuts, False)

    
    @abstractmethod
    def create_top(self, pos: wxPoint, angle: float) -> None:
        pass


    @abstractmethod
    def create_bottom(self, pos: wxPoint, angle: float) -> None:
        pass


    def create_outline(self) -> None:
        self.create_tab()
        segment(
            self.board, 
            wxPoint(self.side * self.length, 0), 
            wxPoint(self.side * self.length, self.height), 
            self.outline_width, 
            Edge_Cuts, 
            False,
        )

        for i in range(self.side):
            self.create_top(wxPoint((i + 1) * self.length, 0), radians(180))
            self.create_bottom(wxPoint(i * self.length, self.height), 0)