import pcbnew
from pcbnew import FromMM

from box import Box
from coil import CoilStyle
import gerber_plot
from schematic import BoxSchematic
import utils

def gen_box(file_name: str, stack_n: int, length: float, coil_d: float = 20, coil_track_w: float = 0.8, coil_track_s: float = 0.6) -> None:
    stack_n = utils.round_to_four(stack_n)
    length = FromMM(length)
    coil_d = FromMM(coil_d)
    coil_track_w = FromMM(coil_track_w)
    coil_track_s = FromMM(coil_track_s)

    if not file_name:
        file_name = 'untitiled_box'
    pcb_path = f'{file_name}.kicad_pcb'
    pcb_path_2 = f'{file_name}_2.kicad_pcb'
    gbr_path = f'Gerber_{file_name}'

    coil_style = CoilStyle(coil_d, coil_track_w, coil_track_s)
    c_val = coil_style.get_cap_repr()
    print('Coil Style:', coil_style, sep='\n')

    sch = BoxSchematic(stack_n, c_val)
    sch.generate_pcb(pcb_path)
    
    board = pcbnew.LoadBoard(pcb_path)
    box = Box(board, sch, coil_style, length, stack_n)
    _generate(box)

    pcbnew.SaveBoard(pcb_path_2, board)
    gerber_plot.generate_gerbers(board, gbr_path)
    gerber_plot.generate_drill_file(board, gbr_path)


def _generate(box: Box) -> None:
    box.layout()
    box.route_caps()
    box.create_outline()
    box.create_coils()
    box.create_foldline()
    box.create_tag_marker()


def main():
    stack_n = 4
    length = 45
    box_file_name = f'box_N{stack_n}_L{length}'
    gen_box(box_file_name, stack_n, length)


if __name__ == '__main__':
    main()