import os
import shutil
import pcbnew
from pcbnew import FromMM

from coil import CoilStyle
import gerber_plot
from schematic import StationSchematic
from station import Station
import utils

def gen_station(project_name: str, stack_n: int, length: float, height: float = 60, coil_d: float = 20, coil_track_w: float = 0.8, coil_track_s: float = 0.6) -> None:
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
        sch = StationSchematic(stack_n, c_val)
        sch.generate_pcb(pcb_path)
        os.chdir(cwd_path)
    except Exception as err:
        with open(log_file, 'a') as file:
            file.write(f'PCB not created\nError: {err}')

    # Layout, route, and draw the PCB
    try:
        board = pcbnew.LoadBoard(pcb_path)
        station = Station(board, sch, coil_style, length, height, stack_n)
        _generate_pre_route(station)

        os.chdir(tmp_path)
        utils.route(board, project_name)
        os.chdir(cwd_path)

        board = pcbnew.LoadBoard(pcb_path)
        station = Station(board, sch, coil_style, length, height, stack_n)
        _generate_post_route(station)
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
    project_name = f'station_N{stack_n}_L{length}'
    gen_station(project_name, stack_n, length)


if __name__ == '__main__':
    main()