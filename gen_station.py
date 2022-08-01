import pcbnew
from pcbnew import FromMM

from coil import CoilStyle
import gerber_plot
from schematic import Schematic
from station import Station
import utils

def main():
    stack_n = utils.round_to_four(8)
    length = FromMM(65)
    height = FromMM(60)
    coil_d = FromMM(20)
    coil_track_w = FromMM(0.8)
    coil_track_s = FromMM(0.6)

    file_name = f'station_out_N{stack_n}'
    pcb_path = f'{file_name}.kicad_pcb'
    pcb_path_2 = f'{file_name}_2.kicad_pcb'
    gbr_path = f'Gerber_{file_name}'

    coil_style = CoilStyle(coil_d, coil_track_w, coil_track_s)
    c_val = coil_style.get_cap_repr()
    print('Coil Style:', coil_style, sep='\n')

    sch = Schematic(stack_n, c_val)
    sch.generate_pcb(pcb_path)
    
    board = pcbnew.LoadBoard(pcb_path)
    station = Station(board, sch, coil_style, length, height, stack_n)
    station.layout()
    station.set_zones()

    utils.route(board, file_name)

    board = pcbnew.LoadBoard(pcb_path)
    station = Station(board, sch, coil_style, length, height, stack_n)
    station.create_outline()
    station.create_coils()
    station.create_foldline()

    pcbnew.SaveBoard(pcb_path_2, board)
    gerber_plot.generate_gerbers(board, gbr_path)
    gerber_plot.generate_drill_file(board, gbr_path)


if __name__ == '__main__':
    main()