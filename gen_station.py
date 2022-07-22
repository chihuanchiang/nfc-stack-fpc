from pcbnew import *
from utils import *
from coil import Coil
from schematic import Schematic
from station import Station
from gerber_plot import generate_drill_file, generate_gerbers


def main():
    max_n = round_to_four(8)
    c_val = '300p'
    length = 65
    height = 60
    coil_d = 20
    coil_turns = 6
    track_w = 0.8
    track_s = 0.6
    file_name = f'station_out_M{max_n}'
    pcb_path = f'{file_name}.kicad_pcb'
    pcb_path_2 = f'{file_name}_2.kicad_pcb'
    gbr_path = f'Gerber_{file_name}'

    sch = Schematic(max_n, c_val)
    sch.generate_pcb(pcb_path)
    
    board = LoadBoard(pcb_path)
    print(board)
    print(type(board))
    print(board.GetFileName())

    coil = Coil(board, FromMM(coil_d), FromMM(track_w), FromMM(track_s), coil_turns)
    station = Station(board, coil, FromMM(length), FromMM(height), max_n, FromMM(0.1))
    station.load_footprints(sch)
    station.layout()
    station.create_outline()

    SaveBoard(pcb_path_2, board)

    generate_gerbers(board, gbr_path)
    generate_drill_file(board, gbr_path)


if __name__ == '__main__':
    main()