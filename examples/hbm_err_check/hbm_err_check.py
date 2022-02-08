import sys
import pathlib
import argparse

lib_path = str(pathlib.Path(__file__).resolve().parents[2])
sys.path.append(lib_path)
from qubelib import *
from qubelib import WaveRamAccess
from qubelib import logger

IP_ADDR = '10.0.0.16'

def main():

    WAVE_RAM_PORT = 0x4000
    wave_ram_access = WaveRamAccess(IP_ADDR, WAVE_RAM_PORT, logger.get_file_logger())
    
    wr_data = bytearray(b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0A\x0B\x0C\x0D\x0E\x0F\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1A\x1B\x1C\x1D\x1E\x1F')
    wave_ram_access.write(0x000000000, wr_data)
    rd_data = wave_ram_access.read(0x000000000, len(wr_data))
    print(len(rd_data))
    for i in range(len(wr_data)):
        print(str(wr_data[i]) + "  " + str(rd_data[i]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--ipaddr')
    args = parser.parse_args()
    if args.ipaddr is not None:
        IP_ADDR = args.ipaddr

    main()
