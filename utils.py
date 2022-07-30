from pcbnew import *
from vector import *
from typing import Dict, List

def get_layer_table(board: BOARD) -> Dict[str, int]:
    return {board.GetLayerName(i): i for i in range(PCB_LAYER_ID_COUNT)}


def segment(board: BOARD, start: wxPoint, end: wxPoint, width: int, layer: int, is_track: bool = True) -> None:
    seg = PCB_TRACK(board) if is_track else PCB_SHAPE(board)
    board.Add(seg)
    seg.SetStart(start)
    seg.SetEnd(end)
    seg.SetWidth(width)
    seg.SetLayer(layer)


def polyline(board: BOARD, points: List[wxPoint], width: int, layer: int, is_track: bool = True) -> None:
    for i in range(len(points) - 1):
        segment(board, points[i], points[i + 1], width, layer, is_track)


def via(board: BOARD, pos: wxPoint, diameter: int, top_layer: int, bottom_layer: int) -> None:
    new_via = PCB_VIA(board)
    board.Add(new_via)
    new_via.SetLayerPair(top_layer, bottom_layer)
    new_via.SetPosition(pos)
    new_via.SetViaType(VIATYPE_THROUGH)
    new_via.SetWidth(diameter)


def round_to_four(n: int) -> int:
    rm = n % 4
    return n if (rm == 0) else n - rm + 4


def add_zone(board: BOARD, x1: int, x2: int, y1: int, y2: int) -> None:
    if x1 > x2:
        x1, x2 = x2, x1
    if y1 > y2:
        y1, y2 = y2, y1
    corners = [wxPoint(x1, y1), wxPoint(x2, y1), wxPoint(x2, y2), wxPoint(x1, y2)]
    new_area: ZONE = board.AddArea(None, 0, F_Cu, corners[0], ZONE_BORDER_DISPLAY_STYLE_DIAGONAL_EDGE)
    new_area.AppendCorner(corners[1], -1)
    new_area.AppendCorner(corners[2], -1)
    new_area.AppendCorner(corners[3], -1)
    new_area.SetIsRuleArea(True)
    new_area.SetDoNotAllowTracks(True)
    new_area.SetDoNotAllowVias(True)
    new_area.SetLayerSet(LSET(F_Cu).AddLayer(B_Cu))


def fold_line(board: BOARD, start: wxPoint, end: wxPoint, diameter: int, distance: int, clearance: int) -> None:
    fp = FOOTPRINT(board)
    fp.SetPosition(wxPoint(0, 0))
    board.Add(fp)

    diff = end - start
    length = mag(diff)
    n = int(length) // distance
    increment = divided(diff, n)
    for i in range(n + 1):
        pos = start + multiplied(increment, i)
        if not hit_something(board, pos, diameter, clearance):
            hole = PAD(fp)
            hole.SetPosition(pos)
            hole.SetDrillSize(wxSize(diameter, diameter))
            hole.SetSize(wxSize(0, 0))
            fp.Add(hole)


def hit_something(board: BOARD, pos: wxPoint, diameter: int, clearance: int) -> bool:
    min_dist = lambda item: (diameter + item.GetWidth()) / 2 + clearance
    return (
        any(dot_to_segment(pos, t.GetStart(), t.GetEnd()) <= min_dist(t) for t in board.GetTracks()) or
        any(dot_to_segment(pos, d.GetStart(), d.GetEnd()) <= min_dist(d) for d in board.GetDrawings())
    )