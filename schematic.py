from skidl import *

class Schematic:

    def __init__(self, N, c_val):
        self.N = N
        c_tmp = Part('Device', 'C', TEMPLATE, footprint='Capacitor_SMD:C_0603_1608Metric')
        self.c_coil = c_tmp(N + 1, value=c_val)
        self.c_mux = c_tmp(value='0.1u')
        self.mux = Part('74xx', 'CD74HC4067M', footprint='Package_SO:SSOP-24_5.3x8.2mm_P0.65mm')
        self.mcu = Part('ARDUINO_PRO_MINI', 'ARDUINO_PRO_MINI', footprint='ARDUINO_PRO_MINI:ARDUINO_PRO_MINI')
        self.head_ant = Part('Connector', 'Conn_01x04_Male', footprint='Connector:NS-Tech_Grove_1x04_P2mm_Vertical')
        self.head_ftdi = Part('Connector', 'Conn_01x04_Male', footprint='Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical')


    def generate_pcb(self, path):
        generate_pcb(file_=path)