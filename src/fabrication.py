import csv
import pcbnew
from typing import Any, Dict, List, Tuple

def _write_csv(path: str, content: List[Dict[str, Any]]) -> None:
    with open(path, 'w', newline='') as file:
        wtr = csv.DictWriter(file, fieldnames=content[0].keys())
        wtr.writeheader()
        wtr.writerows(content)


def _get_capacitors(board: pcbnew.BOARD) -> List[pcbnew.FOOTPRINT]:
    return [fp for fp in board.GetFootprints() if fp.GetReference()[0] == "C"]


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
    return fp.GetDescription()


def _field_pins(fp: pcbnew.FOOTPRINT) -> str:
    return str(len(fp.Pads()))


def export_pos(board: pcbnew.BOARD, path: str) -> None:
    fps = _get_capacitors(board)
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


def export_bom(board: pcbnew.BOARD, path: str) -> None:
    fps = _get_capacitors(board)

    bom: Dict[Tuple[str, str], List[pcbnew.FOOTPRINT]] = {}
    for fp in fps:
        key = (fp.GetValue(), fp.GetFPID().GetUniStringLibId())
        if key in bom:
            bom[key].append(fp)
        else:
            bom[key] = [fp]

    bom = list(bom.values())
    for m in bom:
        m.sort(key=_field_designator)

    bom_info = [
        {
            'Comment': _field_comment(m[0]),
            'Description': _field_description(m[0]),
            'Footprint': _field_footprint(m[0]),
            'Pins': _field_pins(m[0]),
            'Lib-ref': [fp.GetReference() for fp in m],
            'Quantity': len(m),
        }
        for m in bom
    ]

    _write_csv(path, bom_info)