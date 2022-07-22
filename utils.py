from pcbnew import *
from typing import Dict, List, Tuple


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


def via(board: BOARD, pos: wxPoint, width: int, top_layer: int, bottom_layer: int) -> None:
    new_via = PCB_VIA(board)
    board.Add(new_via)
    new_via.SetLayerPair(top_layer, bottom_layer)
    new_via.SetPosition(pos)
    new_via.SetViaType(VIATYPE_THROUGH)
    new_via.SetWidth(width)


def round_to_four(n: int) -> int:
    rm = n % 4
    return n if (rm == 0) else n - rm + 4