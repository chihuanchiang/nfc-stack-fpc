import pcbnew
from pcbnew import FromMM

from box import Box
from coil import CoilStyle
from cuboid import Cuboid
import gerber_plot
import schematic
from station import Station
import utils

def generate(file_name: str, block_type: Cuboid, sch_type: schematic.Schematic, stack_n: int, length: float, height: float = 60, coil_d: float = 20, coil_track_w: float = 0.8, coil_track_s: float = 0.6) -> None:
    stack_n = utils.round_to_four(stack_n)
    length = FromMM(length)
    height = FromMM(height)
    coil_d = FromMM(coil_d)
    coil_track_w = FromMM(coil_track_w)
    coil_track_s = FromMM(coil_track_s)

    if not file_name:
        file_name = 'untitiled'
    pcb_path = f'{file_name}.kicad_pcb'
    gbr_path = f'Gerber_{file_name}'

    coil_style = CoilStyle(coil_d, coil_track_w, coil_track_s)
    c_val = coil_style.get_cap_repr()
    print('Coil Style:', coil_style, sep='\n')

    sch = sch_type(stack_n, c_val)
    sch.generate_pcb(pcb_path)
    
    board = pcbnew.LoadBoard(pcb_path)
    if block_type == Station:
        block = Station(board, sch, coil_style, length, height, stack_n)
    else:
        block = Box(board, sch, coil_style, length, stack_n)
    board = block.create()

    pcbnew.SaveBoard(pcb_path, board)
    gerber_plot.generate_gerbers(board, gbr_path)
    gerber_plot.generate_drill_file(board, gbr_path)


def generate_station(stack_n: int, length: float):
    station_file_name = f'station_N{stack_n}_L{length}'
    generate(station_file_name, Station, schematic.StationSchematic, stack_n, length)


def generate_box(stack_n: int, length: float):
    box_file_name = f'box_N{stack_n}_L{length}'
    generate(box_file_name, Box, schematic.BoxSchematic, stack_n, length)


def main():
    stack_n = 4
    length = 45
    generate_station(stack_n, length)
    # generate_box(stack_n, length)


if __name__ == '__main__':
    main()