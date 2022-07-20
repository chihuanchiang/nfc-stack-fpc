from pcbnew import *
from box import Box
from gerber_plot import generate_drill_file, generate_gerbers


def main():
    board_name = 'box_out_M8'
    board = BOARD()
    board.SetFileName(board_name)
    station = Box(board, FromMM(45), 8, FromMM(0.1))
    station.create_outline()

    output_path = board_name
    generate_gerbers(board, output_path)
    generate_drill_file(board, output_path)


if __name__ == '__main__':
    main()