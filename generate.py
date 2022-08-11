import argparse
import os
import shutil
import pcbnew
from pcbnew import FromMM

from box import Box
from coil import CoilStyle
from cuboid import Cuboid
import fabrication
import gerber_plot
import schematic
from station import Station
import utils

def generate(project_name: str, block_type: Cuboid, sch_type: schematic.Schematic, stack_n: int, length: float, height: float, coil_d: float, coil_track_w: float, coil_track_s: float) -> None:
    stack_n = utils.round_to_four(stack_n)
    length = FromMM(length)
    height = FromMM(height)
    coil_d = FromMM(coil_d)
    coil_track_w = FromMM(coil_track_w)
    coil_track_s = FromMM(coil_track_s)

    # Define paths
    try:
        if not project_name:
            project_name = 'untitled'
        cwd_path = os.getcwd()
        tmp_path = os.path.join(cwd_path, 'tmp').replace('\\', '/')
        tmp_output_path = os.path.join(tmp_path, project_name + '-Gerber').replace('\\', '/')
        pcb_path = os.path.join(tmp_path, project_name + '.kicad_pcb').replace('\\', '/')
        output_path = os.path.join(cwd_path, project_name + '-Gerber').replace('\\', '/')
        pos_path = os.path.join(cwd_path, project_name + '-pos.csv').replace('\\', '/')
        log_file = os.path.join(cwd_path, 'log.txt').replace('\\', '/')
        if os.path.exists(log_file):
            os.remove(log_file)
    except Exception as err:
        with open(log_file, 'a') as file:
            file.write(f'Startup error\nError: {err}\n')

    coil_style = CoilStyle(coil_d, coil_track_w, coil_track_s)
    c_val = coil_style.get_cap_repr()
    print('Coil Style:', coil_style, sep='\n')

    # Create a temp folder
    try:
        os.mkdir(tmp_path)
    except Exception as err:
        with open(log_file, 'a') as file:
            file.write('tmp folder not created\nError:{}\n'.format(err))

    # Create a PCB from schematic
    try:
        os.chdir(tmp_path)
        sch = sch_type(stack_n, c_val)
        sch.generate_pcb(pcb_path)
        os.chdir(cwd_path)
    except Exception as err:
        with open(log_file, 'a') as file:
            file.write(f'PCB not created\nError: {err}')

    # Layout, route, and outline the PCB
    try:
        board = pcbnew.LoadBoard(pcb_path)
        if block_type == Station:
            block = Station(board, sch, coil_style, length, height, stack_n)
        else:
            block = Box(board, sch, coil_style, length, stack_n)
        board = block.create()
    except Exception as err:
        with open(log_file, 'a') as file:
            file.write(f'PCB not finished\nError: {err}')

    # Plot Gerbers
    try:
        gerber_plot.generate_gerbers(board, tmp_output_path)
    except Exception as err:
        with open(log_file, 'a') as file:
            file.write(f'Gerbers not plotted\nError: {err}')

    # Plot drill file
    try:
        gerber_plot.generate_drill_file(board, tmp_output_path)
    except Exception as err:
        with open(log_file, 'a') as file:
            file.write(f'Drill file not plotted\nError: {err}')

    # Create compressed file from tmp
    try:
        os.chdir(tmp_output_path)
        shutil.make_archive(output_path, 'zip')
        os.chdir(cwd_path)
    except Exception as err:
        with open(log_file, 'a') as file:
            file.write(f'ZIP file not created\nError: {err}')

    # Export pick and place (pos) file
    try:
        fabrication.export_pos(board, pos_path)
    except Exception as err:
        with open(log_file, 'a') as file:
            file.write(f'pos file not exported\nError: {err}')

    # Remove temp folder
    try:
        shutil.rmtree(tmp_path, ignore_errors=True)
    except Exception as err:
        with open(log_file, 'a') as file:
            file.write('temp folder not deleted\nError: {}\n'.format(err))


def export_config(path: str, config: dict) -> None:
    with open(path, 'w') as file:
        for k, v in config.items():
            file.write(f'{k}: {v}\n')


def main():
    parser = argparse.ArgumentParser(
        description='Generates fabrication files for NFCStack boxes and stations. All lengths are measured in mm.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-b', '--box', action='store_true', help='Generate a box if specified, otherwise generate a station.')
    parser.add_argument('-H', '--height', type=float, default=60, help='Height. Only applies to stations.')
    parser.add_argument('-d', '--diameter', type=float, default=20, help='Coil diameter')
    parser.add_argument('-w', '--track-width', type=float, default=0.8, help='Coil track width')
    parser.add_argument('-s', '--track-space', type=float, default=0.6, help='Space between coil tracks')
    parser.add_argument('file', type=str, help='File name')
    parser.add_argument('size', type=float, help='Size')
    parser.add_argument('layers', type=int , help='Maximum layers of stacking')
    args = parser.parse_args()
    export_config('config.txt', vars(args))

    if args.box:
        block_type = Box
        sch_type = schematic.BoxSchematic
    else:
        block_type = Station
        sch_type = schematic.StationSchematic
    generate(args.file, block_type, sch_type, args.layers, args.size, args.height, args.diameter, args.track_width, args.track_space)

if __name__ == '__main__':
    main()