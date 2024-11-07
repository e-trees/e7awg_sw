import argparse
from e7awgsw.udpaccess import WaveRamAccess
from e7awgsw.hwparam import WaveRamParamsSimpleMulti
from e7awgsw.logger import get_file_logger

IP_ADDR = '10.0.0.16'

def main():

    wave_ram_params = WaveRamParamsSimpleMulti()
    wave_ram_access = WaveRamAccess(
        IP_ADDR, wave_ram_params.udp_port(), wave_ram_params.word_size(), get_file_logger())
    
    wr_data = bytearray(b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0A\x0B\x0C\x0D\x0E\x0F\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1A\x1B\x1C\x1D\x1E\x1F')
    wave_ram_access.write(0x000000000, wr_data)
    rd_data = wave_ram_access.read(0x000000000, len(wr_data))
    print(len(rd_data))
    for i in range(len(wr_data)):
        print(str(wr_data[i]) + "  " + str(rd_data[i]))
    wave_ram_access.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--ipaddr')
    args = parser.parse_args()
    if args.ipaddr is not None:
        IP_ADDR = args.ipaddr

    main()
