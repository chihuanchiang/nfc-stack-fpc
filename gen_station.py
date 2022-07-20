from pcbnew import *
from station import Station
from schematic import Schematic
from gerber_plot import generate_drill_file, generate_gerbers


def main():
    channel = 8
    c_val = '300p'
    length = 45
    height = 60
    file_name = f'station_out_M{channel}'
    pcb_path = f'{file_name}.kicad_pcb'
    gbr_path = f'Gerber_{file_name}'

    sch = Schematic(channel, c_val)
    sch.generate_pcb(pcb_path)
    
    board = LoadBoard(pcb_path)
    # board = BOARD()
    # board.SetFileName(file_name)
    print(board)
    print(type(board))
    print(board.GetFileName())
    move_fps(board, wxPointMM(40, 40))
    station = Station(board, FromMM(length), FromMM(height), channel, FromMM(0.1))
    # station.create_outline()

    generate_gerbers(board, gbr_path)
    generate_drill_file(board, gbr_path)


def move_fps(board: BOARD, v: wxPoint) -> None:
    fps = board.GetFootprints()
    for fp in fps:
        fp.SetPosition(fp.GetPosition() + v)


if __name__ == '__main__':
    main()