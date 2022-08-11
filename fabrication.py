import csv
import pcbnew
from typing import Any, Dict, List

def _write_csv(path: str, content: List[Dict[str, Any]]) -> None:
    with open(path, 'w', newline='') as file:
        wtr = csv.DictWriter(file, fieldnames=content[0].keys())
        wtr.writeheader()
        wtr.writerows(content)


def _field_designator(fp: pcbnew.FOOTPRINT) -> str:
    return fp.GetReference()


def _field_footprint(fp: pcbnew.FOOTPRINT) -> str:
    return fp.GetFPID().GetUniStringLibId()


def _field_mid_x(fp: pcbnew.FOOTPRINT) -> str:
    return '%.6f' % pcbnew.ToMM(fp.GetX())


def _field_mid_y(fp: pcbnew.FOOTPRINT) -> str:
    return '%.6f' % pcbnew.ToMM(-fp.GetY())


def _field_layer(fp: pcbnew.FOOTPRINT) -> str:
    return 'T' if fp.GetLayer() == pcbnew.F_Cu else 'B'


def _field_rotation(fp: pcbnew.FOOTPRINT) -> str:
    return str(int(fp.GetOrientationDegrees()))


def _field_comment(fp: pcbnew.FOOTPRINT) -> str:
    return fp.GetValue()


def _field_description(fp: pcbnew.FOOTPRINT) -> str:
    return None


def _field_pins(fp: pcbnew.FOOTPRINT) -> str:
    return str(len(fp.Pads()))


def export_pos(board: pcbnew.BOARD, path: str) -> None:
    fps = board.GetFootprints()
    fps.sort(key=_field_designator)
    pos_info = [
        {
            'Designator': _field_designator(fp),
            'Footprint': _field_footprint(fp),
            'Mid X mm': _field_mid_x(fp),
            'Mid Y mm': _field_mid_y(fp),
            'Layer': _field_layer(fp),
            'Rotation': _field_rotation(fp),
            'Comment': _field_comment(fp),
        }
        for fp in fps
    ]
    _write_csv(path, pos_info)