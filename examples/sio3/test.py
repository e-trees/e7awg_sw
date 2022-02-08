import sys
import os
import pathlib
import math
import argparse
from collections import namedtuple

lib_path = str(pathlib.Path(__file__).resolve().parents[2])
sys.path.append(lib_path)
#from qubelib import *
import qubelib

IP_ADDR = '10.1.0.12'

wave_params = namedtuple(
    'WaveParams',
    ('num_wait_words',
     'ctrl_freq',
     'ctrl_wave_len',
     'readout_freq',
     'readout_wave_len',
     'num_readout_blank',
     'num_chunk_repeats'))

def main(wave_params):
    awg_ctrl = qubelib.AwgCtrl(IP_ADDR)
    print(awg_ctrl)

if __name__ == "__main__":
    ctrl_wave_len = 10
    
    wparams = wave_params(
        num_wait_words = 0,
        ctrl_freq = 100, # MHz
        ctrl_wave_len = ctrl_wave_len, # ns
        readout_freq = 100, # MHz
        readout_wave_len = 2000, # ns
        num_readout_blank = 0.1, # ms
        num_chunk_repeats = 10000, # num of summation
    )
    print(int(qubelib.AWG.U13))

    main(wparams)
