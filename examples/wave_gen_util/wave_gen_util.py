"""
パラメータを指定して波形を生成するユーティリティクラスの使い方を示す
"""
import sys
import os
import pathlib
import math

lib_path = str(pathlib.Path(__file__).resolve().parents[2])
sys.path.append(lib_path)
from qubelib import *

def to_degree(val):
    return 180 * val / math.pi

if __name__ == "__main__":
    dir = "./result/"
    os.makedirs(dir, exist_ok = True)

    # sin
    wave = SinWave(num_cycles = 2, frequency = 5e6, amplitude = 1000)
    plot_graph(
        AwgCtrl.SAMPLING_RATE,
        wave.gen_samples(AwgCtrl.SAMPLING_RATE), 
        "sin [cycles:{}, freq:{} [MHz], amp:{}, phase:{}, offset:{}]"
        .format(wave.num_cycles, wave.frequency/1e6, wave.amplitude, to_degree(wave.phase), wave.offset), 
        dir + "000.png", 
        '#b44c97')

    # cos
    wave = SinWave(num_cycles = 3, frequency = 5e6, amplitude = 2000, phase = math.pi / 2)
    plot_graph(
        AwgCtrl.SAMPLING_RATE,
        wave.gen_samples(AwgCtrl.SAMPLING_RATE), 
        "sin [cycles:{}, freq:{} [MHz], amp:{}, phase:{}, offset:{}]"
        .format(wave.num_cycles, wave.frequency/1e6, wave.amplitude, to_degree(wave.phase), wave.offset), 
        dir + "001.png", 
        '#b44c97')
    
    # sawtooth  crest_pos = 0.0
    wave = SawtoothWave(num_cycles = 3, frequency = 1e6, amplitude = 1000, crest_pos = 0.0)
    plot_graph(
        AwgCtrl.SAMPLING_RATE,
        wave.gen_samples(AwgCtrl.SAMPLING_RATE), 
        "sawtooth [cycles:{}, freq:{} [MHz], amp:{}, phase:{}, offset:{}, crest pos:{}]"
        .format(wave.num_cycles, wave.frequency/1e6, wave.amplitude, to_degree(wave.phase), wave.offset, wave.crest_pos), 
        dir + "002.png", 
        '#b44c97')

    # sawtooth  crest_pos = 0.5
    wave = SawtoothWave(num_cycles = 3, frequency = 1e6, amplitude = 1000, crest_pos = 0.5)
    plot_graph(
        AwgCtrl.SAMPLING_RATE,
        wave.gen_samples(AwgCtrl.SAMPLING_RATE), 
        "sawtooth [cycles:{}, freq:{} [MHz], amp:{}, phase:{}, offset:{}, crest pos:{}]"
        .format(wave.num_cycles, wave.frequency/1e6, wave.amplitude, to_degree(wave.phase), wave.offset, wave.crest_pos), 
        dir + "003.png", 
        '#b44c97')

    # sawtooth  crest_pos = 1.0
    wave = SawtoothWave(num_cycles = 3, frequency = 1e6, amplitude = 1000, crest_pos = 1.0)
    plot_graph(
        AwgCtrl.SAMPLING_RATE,
        wave.gen_samples(AwgCtrl.SAMPLING_RATE), 
        "sawtooth [cycles:{}, freq:{} [MHz], amp:{}, phase:{}, offset:{}, crest pos:{}]"
        .format(wave.num_cycles, wave.frequency/1e6, wave.amplitude, to_degree(wave.phase), wave.offset, wave.crest_pos), 
        dir + "004.png", 
        '#b44c97')

    # square  duty = 0.5
    wave = SquareWave(num_cycles = 2, frequency = 2e6, amplitude = 1000, duty_cycle = 0.5)
    plot_graph(
        AwgCtrl.SAMPLING_RATE,
        wave.gen_samples(AwgCtrl.SAMPLING_RATE), 
        "square [cycles:{}, freq:{} [MHz], amp:{}, phase:{}, offset:{}, duty cycle:{}]"
        .format(wave.num_cycles, wave.frequency/1e6, wave.amplitude, to_degree(wave.phase), wave.offset, wave.duty_cycle), 
        dir + "005.png", 
        '#b44c97')

    # square  duty = 0.8, offset = 1000
    wave = SquareWave(num_cycles = 2, frequency = 2e6, amplitude = 1000, offset = 1000, duty_cycle = 0.8)
    plot_graph(
        AwgCtrl.SAMPLING_RATE,
        wave.gen_samples(AwgCtrl.SAMPLING_RATE), 
        "square [cycles:{}, freq:{} [MHz], amp:{}, phase:{}, offset:{}, duty cycle:{}]"
        .format(wave.num_cycles, wave.frequency/1e6, wave.amplitude, to_degree(wave.phase), wave.offset, wave.duty_cycle), 
        dir + "006.png", 
        '#b44c97')
