import math
import os
import pcbnew
from pcbnew import wxPoint, BOARD
from typing import Dict, List

import vector

def get_layer_table(board: BOARD) -> Dict[str, int]:
    return {board.GetLayerName(i): i for i in range(pcbnew.PCB_LAYER_ID_COUNT)}


def segment(board: BOARD, start: wxPoint, end: wxPoint, width: int, layer: int, is_track: bool = True) -> None:
    seg = pcbnew.PCB_TRACK(board) if is_track else pcbnew.PCB_SHAPE(board)
    board.Add(seg)
    seg.SetStart(start)
    seg.SetEnd(end)
    seg.SetWidth(width)
    seg.SetLayer(layer)


def circle(board: BOARD, pos: wxPoint, diameter: int, width: int, layer: int, is_track: bool = True, detail: int = 20) -> None:
    curr = wxPoint(diameter / 2, 0)
    points = [vector.rotated(curr, 2 * math.pi * i / detail) + pos for i in range(detail + 1)]
    polyline(board, points, width, layer, is_track)


def polyline(board: BOARD, points: List[wxPoint], width: int, layer: int, is_track: bool = True) -> None:
    for i in range(len(points) - 1):
        segment(board, points[i], points[i + 1], width, layer, is_track)


def via(board: BOARD, pos: wxPoint, diameter: int, top_layer: int, bottom_layer: int) -> None:
    new_via = pcbnew.PCB_VIA(board)
    board.Add(new_via)
    new_via.SetLayerPair(top_layer, bottom_layer)
    new_via.SetPosition(pos)
    new_via.SetViaType(pcbnew.VIATYPE_THROUGH)
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
    new_area: pcbnew.ZONE = board.AddArea(None, 0, pcbnew.F_Cu, corners[0], pcbnew.ZONE_BORDER_DISPLAY_STYLE_DIAGONAL_EDGE)
    new_area.AppendCorner(corners[1], -1)
    new_area.AppendCorner(corners[2], -1)
    new_area.AppendCorner(corners[3], -1)
    new_area.SetIsRuleArea(True)
    new_area.SetDoNotAllowTracks(True)
    new_area.SetDoNotAllowVias(True)
    new_area.SetLayerSet(pcbnew.LSET(pcbnew.F_Cu).AddLayer(pcbnew.B_Cu))


def fold_line(board: BOARD, start: wxPoint, end: wxPoint, diameter: int, distance: int, outline_width: int, clearance: int) -> None:
    diff = end - start
    length = vector.mag(diff)
    n = int(length) // distance
    increment = vector.divided(diff, n)
    for i in range(n + 1):
        pos = start + vector.multiplied(increment, i)
        if not hit_something(board, pos, diameter, clearance):
            circle(board, pos, diameter, outline_width, pcbnew.Edge_Cuts, False)


def hit_something(board: BOARD, pos: wxPoint, diameter: int, clearance: int) -> bool:
    min_dist = lambda item: (diameter + item.GetWidth()) / 2 + clearance
    return (
        any(vector.dot_to_segment(pos, t.GetStart(), t.GetEnd()) <= min_dist(t) for t in board.GetTracks()) or
        any(vector.dot_to_segment(pos, d.GetStart(), d.GetEnd()) <= min_dist(d) for d in board.GetDrawings())
    )


def route(board: BOARD, path: str) -> None:
    curr_dir = os.path.dirname(__file__)
    router_path = os.path.join(curr_dir, './tools/freerouting-1.6.2.jar')
    dsn_path = f'{path}.dsn'
    ses_path = f'{path}.ses'

    if not pcbnew.ExportSpecctraDSN(board, dsn_path):
        msg = f'Can not export specctra dsn file: {dsn_path}'
        raise Exception(msg)
    if os.system(f'java -jar {router_path} -de {dsn_path} -do {ses_path} -mp 100 -us global') != 0:
        raise Exception('Autorouting failed')

    print(
        '============================================================',
        'Freerouting has successfully routed your pcb',
        f'1. Open {board.GetFileName()} in KiCad and import specctra session file: {ses_path}',
        '   File > Import > Specctra Section...',
        '2. Save the file',
        '   File > Save or cmd + s',
        '============================================================',
        sep='\n',
    )
    return input('Finished? [y/n]').lower() == 'y'