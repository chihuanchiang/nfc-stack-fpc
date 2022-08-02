import pcbnew
from pcbnew import FromMM

from coil import CoilStyle
import gerber_plot
from schematic import StationSchematic
from station import Station
import utils

def gen_station(file_name: str, stack_n: int, length: float, height: float = 60, coil_d: float = 20, coil_track_w: float = 0.8, coil_track_s: float = 0.6) -> None:
    stack_n = utils.round_to_four(stack_n)
    length = FromMM(length)
    height = FromMM(height)
    coil_d = FromMM(coil_d)
    coil_track_w = FromMM(coil_track_w)
    coil_track_s = FromMM(coil_track_s)

    if not file_name:
        file_name = 'untitiled_station'
    pcb_path = f'{file_name}.kicad_pcb'
    pcb_path_2 = f'{file_name}_2.kicad_pcb'
    gbr_path = f'Gerber_{file_name}'

    coil_style = CoilStyle(coil_d, coil_track_w, coil_track_s)
    c_val = coil_style.get_cap_repr()
    print('Coil Style:', coil_style, sep='\n')

    sch = StationSchematic(stack_n, c_val)
    sch.generate_pcb(pcb_path)
    
    board = pcbnew.LoadBoard(pcb_path)
    station = Station(board, sch, coil_style, length, height, stack_n)
    _generate_pre_route(station)

    utils.route(board, file_name)

    board = pcbnew.LoadBoard(pcb_path)
    station = Station(board, sch, coil_style, length, height, stack_n)
    _generate_post_route(station)

    pcbnew.SaveBoard(pcb_path_2, board)
    gerber_plot.generate_gerbers(board, gbr_path)
    gerber_plot.generate_drill_file(board, gbr_path)


def _generate_pre_route(station: Station) -> None:
    station.layout()
    station.set_zones()


def _generate_post_route(station: Station) -> None:
    station.create_outline()
    station.create_coils()
    station.create_foldline()


def main():
    stack_n = 4
    length = 45
    station_file_name = f'station_N{stack_n}_L{length}'
    gen_station(station_file_name, stack_n, length)


if __name__ == '__main__':
    main()