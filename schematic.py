from abc import ABC, abstractmethod

import skidl
from skidl import Part, Net

class Schematic(ABC):

    @abstractmethod
    def __init__(self, stack_n: int, c_val: str):
        pass

    def generate_pcb(self, path: str) -> None:
        skidl.generate_pcb(file_=path)


class StationSchematic(Schematic):

    def __init__(self, stack_n: int, c_val: str):
        self.c_tmp = Part('Device', 'C', skidl.TEMPLATE, footprint='Capacitor_SMD:C_0603_1608Metric')
        self.c_coil = self.c_tmp(stack_n + 1, value=c_val)
        self.c_mux = self.c_tmp(value='0.1uF')
        self.mux = Part('74xx', 'CD74HC4067M', footprint='Package_SO:SSOP-24_5.3x8.2mm_P0.65mm')
        self.mcu = Part('ARDUINO_PRO_MINI', 'ARDUINO_PRO_MINI', footprint='ARDUINO_PRO_MINI:ARDUINO_PRO_MINI')
        self.head_ant = Part('Connector', 'Conn_01x04_Male', footprint='Connector:NS-Tech_Grove_1x04_P2mm_Vertical')
        self.head_ftdi = Part('Connector', 'Conn_01x04_Male', footprint='Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical')

        self.vcc = Net('VCC')
        self.gnd = Net('GND')
        self.tx = Net('TX')
        self.rx = Net('RX')
        self.sda = Net('SDA')
        self.scl = Net('SCL')

        # self.c_mux[:] += NC # type: ignore
        # self.mux[:] += NC # type: ignore
        # self.head_ant[:] += NC # type: ignore
        # self.head_ftdi[:] += NC # type: ignore
        # for part in self.c_coil:
        #     part[:] += NC # type: ignore
        # for pin in self.mcu:
        #     pin += NC # type: ignore

        self.vcc += self.mcu['VCC'], self.head_ant[2], self.head_ftdi[2], self.c_mux[1], self.mux['VCC']
        self.gnd += self.mcu['GND'], self.head_ant[1], self.head_ftdi[1], self.c_mux[2], self.mux['GND']
        self.tx += self.mcu['TXO'], self.head_ftdi[4]
        self.rx += self.mcu['RXI'], self.head_ftdi[3]
        self.sda += self.mcu['A4'], self.head_ant[3]
        self.scl += self.mcu['A5'], self.head_ant[4]
        self.mux['S0'] += self.mcu['D7']
        self.mux['S1'] += self.mcu['D6']
        self.mux['S2'] += self.mcu['D5']
        self.mux['S3'] += self.mcu['D4']

        for i in range(stack_n):
            self.mux['COM'] & self.c_coil[-1] & self.c_coil[i] & self.mux[f'I{i}']


class BoxSchematic(Schematic):

    def __init__(self, stack_n: int, c_val: str):
        self.c_tmp = Part('Device', 'C', skidl.TEMPLATE, footprint='Capacitor_SMD:C_0603_1608Metric')
        self.c_coil_top = self.c_tmp(stack_n - 1, value = c_val)
        self.c_coil_bottom = self.c_tmp(stack_n - 1, value = c_val)

        for ct, cb in zip(self.c_coil_top, self.c_coil_bottom):
            ct | cb