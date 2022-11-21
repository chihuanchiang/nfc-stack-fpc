# FPC Generator

FPC generator is a python module that lets you design foldable FPCs for NFCStack fast-assembly fabrication.
Specify the size and the maximum stack height you want your system to have, and FPC generator will generate the Gerber files and drill file for manufacturing.

## Usage

`generate.py` can be used as a stand-alone tool to generate files for manufacturing, it can also be used as a module to provide other scripts with the ability to generate those files.

```plain
usage: generate.py [-h] [-b] [-H HEIGHT] [-d DIAMETER] [-w TRACK_WIDTH] [-s TRACK_SPACE] [-k] file size layers

Generates fabrication files for NFCStack boxes and stations. All lengths are measured in mm.

positional arguments:
  file                  File name
  size                  Size
  layers                Maximum layers of stacking

optional arguments:
  -h, --help            show this help message and exit
  -b, --box             Generate a box if specified, otherwise generate a station. (default: False)
  -H HEIGHT, --height HEIGHT
                        Height. Only applies to stations. (default: 60)
  -d DIAMETER, --diameter DIAMETER
                        Coil diameter (default: 20)
  -w TRACK_WIDTH, --track-width TRACK_WIDTH
                        Coil track width (default: 0.8)
  -s TRACK_SPACE, --track-space TRACK_SPACE
                        Space between coil tracks (default: 0.6)
  -k, --keep-tmp-files  Keep temporary files (default: False)
```

### Examples

The following command would generate files for a box design named *mybox* with 45mm length supporting 4 layers of stacking:

```sh
kipython generate.py mybox 45 4 -b
```

> `kipython` is an alias for the Python interperter included with KiCad. More on this later.

This command creates the following files in the current working directory:

- *mybox-Gerber.zip*: Gerber files and drill file for FPC manufacturing
- *mybox-pos.csv*: centroid file for pick and place
- *mybox-bom.csv*: bill of materials for pick and place
- *config.txt*: a record of design parameters
- *generate.erc*: error log
- *generate.log*: error log
- *log.txt*: error log

The following command would generate files for a station design named *mystation* with 63mm length, 70mm height, and supports 8 layers of stacking. Use the `-k` option to keep temporary files, including editable `.kicad_pcb` files.

```sh
kipython generate.py mystation 63 8 -H 70 -k
```

## Installation

FPC generator requires `pcbnew`, `skidl` and `eseries`.

### KiCad (pcbnew)

KiCad is an open source EDA suite, and PcbNew is KiCad's PCB editor. FPC generator uses the module `pcbnew` to create circuit layouts, draw fold lines and outlines for NFCStack stations and boxes.

To use `pcbnew`, download and install [KiCad](https://www.kicad.org/download/). Compatibility is not guaranteed for versions older than `v6.0.5-0`.

KiCad comes with its own Python interpreter, which is installed with `pcbnew` out of the box, namely *KiPython*. Please install SKiDL on, set environment variables to, and run `generate.py` with KiPython. To make code execution and the following installation easier, set a symbolic link to or an alias of KiPython.

The following command creates a symbolic link to KiPython:

```sh
sudo ln -s YOUR_KIPYTHON_PATH /usr/bin/kipython
```

> `YOUR_KIPYTHON_PATH` depends on OS. It may be `/Applications/KiCad/KiCad.app/contents/frameworks/python.framework/versions/3.8/bin/python3` in MacOS.

Adding the following command to `~/.zshrc` creates an alias of KyPython:

```sh
alias kipython=YOUR_KIPYTHON_PATH
```

### SKiDL

[SKiDL](https://devbisme.github.io/skidl/) is a module that lets you describe circuits using Python. FPC generator creates components and their footprints with `skidl`.

The following command installs `skidl`:

```sh
kipython -m pip install skidl
```

#### Setting Environment Variables

Add these lines to `~/.zshrc` so that `skidl` can find KiCad's symbol and footprint library:

```sh
export KICAD_SYMBOL_DIR="/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/"
export KICAD6_FOOTPRINT_DIR="/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/"
```

The exact path may differ from the example. To find the correct path on your OS:

1. Open KiCad
1. Open PCB Editor
1. Go to `Preferences -> Configure Path`
1. For `KICAD_SYMBOL_DIR`, copy the path from `KICAD6_SYMBOL_DIR`
1. For `KICAD6_FOOTPRINT_DIR`, copy the path from `KICAD6_FOOTPRINT_DIR`

#### Upgrading Dependencies

`kinet2pcb` is a module that comes with KiPython, and `skidl` uses this module to create files that can be processed with `pcbnew`. Upgrade it if it's older than `v1.0.1` (or just upgrade it anyway):

```sh
kipython -m pip install --upgrade kinet2pcb
```

`kinet2pcb` can't find the directory to *fp-lib-table* in some OSs. In this case:

1. Find the directory to *fp-lib-table* and copy it.
1. Add the directory to the list `paths` in `kinet2pcb.py::get_global_fp_lib_table_fn()`

> The directory to *fp-lib-table* depends on OS. It may be `~/Library/Preferences/kicad/6.0` in MacOS.

### E-series

The [E-series](https://pypi.org/project/eseries/) is a system of preferred numbers used with electronic components such as resistors and capacitors.
FPC generator rounds the required capacitance to the nearest E-series value before writing it into the BOM (Bill of Materials) and centroid file.

The following command installs `eseries`:

```sh
kipython -m pip install eseries
```

## Adding Symbols and Footprints to the Library

### Symbols

Arduino Pro Mini is not in KiCad's symbol library.

1. Copy *symbols/ARDUINO_PRO_MINI.lib* from the package and paste it to the symbol directory, i.e. your `KICAD_SYMBOL_DIR`.
1. Add this entry to the list in *sym-lib-table*:

```clojure
(lib (name "ARDUINO_PRO_MINI")(type "legacy")(uri "${KICAD6_SYMBOL_DIR}/ARDUINO_PRO_MINI.lib")(options "")(descr "Arduino Pro Mini symbols"))
```

> The directory to *sym-lib-table* depends on OS. It may be `~/Library/Preferences/kicad/6.0` in MacOS.

### Footprints

Arduino Pro Mini and the multiplexer breakout are not in KiCad's footprint library.

1. Copy *footprints/ARDUINO_PRO_MINI*, and *footprints/breakout* from the package and paste them to the footprint directory, i.e. your `KICAD6_FOOTPRINT_DIR`.
1. Add these entries to the list in *fp-lib-table*:

```clojure
(lib (name ARDUINO_PRO_MINI)(type KiCad)(uri ${KICAD6_FOOTPRINT_DIR}/ARDUINO_PRO_MINI)(options "")(descr "Arduino Pro Mini"))
(lib (name Breakout)(type KiCad)(uri ${KICAD6_FOOTPRINT_DIR}/Breakout)(options "")(descr "Breakout Boards"))
```

> The directory to *fp-lib-table* depends on OS. It may be `~/Library/Preferences/kicad/6.0` in MacOS.

## Developing the Software Tool

### Learning Resources

- PcbNew
  - [Documentation](https://docs.kicad.org/doxygen-python/namespacepcbnew.html)
  - [Blog](https://kicad.mmccoo.com/)
  - [Video guide](https://youtu.be/_zVJ96SdYrs)
- SKiDL
  - [Repository](https://github.com/devbisme/skidl)
  - [Documentation](https://devbisme.github.io/skidl/)
  - [Video guide](https://youtu.be/WErQYI2A36M)

### Using VS Code

Configure VS Code to Use KiPython, so that it gives useful prompts for the modules you installed:

1. Install the [Python extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python) from Microsoft
1. Enter `Python: Select Interpreter` in the command palette
1. Add `YOUR_KIPYTHON_PATH`

> `YOUR_KIPYTHON_PATH` depends on OS. It may be `/Applications/KiCad/KiCad.app/contents/frameworks/python.framework/versions/3.8/bin/python3` in MacOS.

### Using the KiPython Console

You may want to test your ideas in the KiPython console as you can modify and observe the circuit layout with both the scripting API and the GUI. Set KiCad's environment variables so that `skidl` can find KiCad's symbol library when run in the KiPython console:

1. Open KiCad GUI and go to `Preferences -> Configure Path`.
1. Copy the directory from `KICAD6_SYMBOL_DIR`.
1. Add a path `KICAD_SYMBOL_DIR` to the copied directory.
