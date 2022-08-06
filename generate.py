import os
import shutil
import pcbnew
from pcbnew import FromMM

from box import Box
from coil import CoilStyle
from cuboid import Cuboid
import gerber_plot
import schematic
from station import Station
import utils

def generate(project_name: str, block_type: Cuboid, sch_type: schematic.Schematic, stack_n: int, length: float, height: float = 60, coil_d: float = 20, coil_track_w: float = 0.8, coil_track_s: float = 0.6) -> None:
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

    # Remove temp folder
    try:
        shutil.rmtree(tmp_path, ignore_errors=True)
    except Exception as err:
        with open(log_file, 'a') as file:
            file.write('temp folder not deleted\nError: {}\n'.format(err))


def generate_station(stack_n: int, length: float):
    project_name = f'station_N{stack_n}_L{length}'
    generate(project_name, Station, schematic.StationSchematic, stack_n, length)


def generate_box(stack_n: int, length: float):
    project_name = f'box_N{stack_n}_L{length}'
    generate(project_name, Box, schematic.BoxSchematic, stack_n, length)


def main():
    stack_n = 4
    length = 45
    generate_station(stack_n, length)
    # generate_box(stack_n, length)


if __name__ == '__main__':
    main()