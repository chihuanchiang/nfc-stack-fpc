from pcbnew import *
from utils import *
from coil import CoilStyle
from schematic import Schematic
from station import Station
from gerber_plot import generate_drill_file, generate_gerbers

def main():
    stack_n = round_to_four(8)
    c_val = '300p'
    length = FromMM(65)
    height = FromMM(60)
    coil_d = FromMM(20)
    coil_turns = 6
    coil_track_w = FromMM(0.8)
    coil_track_s = FromMM(0.6)

    file_name = f'station_out_N{stack_n}'
    pcb_path = f'{file_name}.kicad_pcb'
    pcb_path_2 = f'{file_name}_2.kicad_pcb'
    gbr_path = f'Gerber_{file_name}'

    sch = Schematic(stack_n, c_val)
    sch.generate_pcb(pcb_path)
    
    coil_style = CoilStyle(coil_d, coil_track_w, coil_track_s, coil_turns)
    board = LoadBoard(pcb_path)
    station = Station(board, sch, coil_style, length, height, stack_n)
    station.layout()
    station.set_zones()

    route(board, file_name)

    board = LoadBoard(pcb_path)
    station = Station(board, sch, coil_style, length, height, stack_n)
    station.create_outline()
    station.create_coils()
    station.create_foldline()

    SaveBoard(pcb_path_2, board)
    generate_gerbers(board, gbr_path)
    generate_drill_file(board, gbr_path)


def route(board: BOARD, path: str) -> None:
    from os import system
    router_path = '~/Downloads/freerouting-1.6.2.jar'
    dsn_path = f'{path}.dsn'
    ses_path = f'{path}.ses'

    if not ExportSpecctraDSN(board, dsn_path):
        msg = f'Can not export specctra dsn file: {dsn_path}'
        raise Exception(msg)
    if system(f'java -jar {router_path} -de {dsn_path} -do {ses_path} -mp 100 -us global') != 0:
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


if __name__ == '__main__':
    main()