"""
パラメータを指定して波形を生成するユーティリティクラスの使い方を示す
"""
import os
import math
from e7awgsw import SinWave, SawtoothWave, SquareWave, GaussianPulse, plot_graph, E7AwgHwSpecs, E7AwgHwType

def to_degree(val):
    return 180 * val / math.pi

if __name__ == "__main__":
    dir = "./result/"
    os.makedirs(dir, exist_ok = True)
    sampling_rate = E7AwgHwSpecs(E7AwgHwType.SIMPLE_MULTI).awg.sampling_rate

    # sin
    wave = SinWave(num_cycles = 2, frequency = 5e6, amplitude = 1000)
    plot_graph(
        sampling_rate,
        wave.gen_samples(sampling_rate), 
        "sin [cycles:{}, freq:{} [MHz], amp:{}, phase:{}, offset:{}]"
        .format(wave.num_cycles, wave.frequency/1e6, wave.amplitude, to_degree(wave.phase), wave.offset), 
        dir + "000.png", 
        '#b44c97')

    # cos
    wave = SinWave(num_cycles = 3, frequency = 5e6, amplitude = 2000, phase = math.pi / 2)
    plot_graph(
        sampling_rate,
        wave.gen_samples(sampling_rate), 
        "sin [cycles:{}, freq:{} [MHz], amp:{}, phase:{}, offset:{}]"
        .format(wave.num_cycles, wave.frequency/1e6, wave.amplitude, to_degree(wave.phase), wave.offset), 
        dir + "001.png", 
        '#b44c97')
    
    # sawtooth  crest_pos = 0.0
    wave = SawtoothWave(num_cycles = 3, frequency = 1e6, amplitude = 1000, crest_pos = 0.0)
    plot_graph(
        sampling_rate,
        wave.gen_samples(sampling_rate), 
        "sawtooth [cycles:{}, freq:{} [MHz], amp:{}, phase:{}, offset:{}, crest pos:{}]"
        .format(wave.num_cycles, wave.frequency/1e6, wave.amplitude, to_degree(wave.phase), wave.offset, wave.crest_pos), 
        dir + "002.png", 
        '#b44c97')

    # sawtooth  crest_pos = 0.5
    wave = SawtoothWave(num_cycles = 3, frequency = 1e6, amplitude = 1000, crest_pos = 0.5)
    plot_graph(
        sampling_rate,
        wave.gen_samples(sampling_rate), 
        "sawtooth [cycles:{}, freq:{} [MHz], amp:{}, phase:{}, offset:{}, crest pos:{}]"
        .format(wave.num_cycles, wave.frequency/1e6, wave.amplitude, to_degree(wave.phase), wave.offset, wave.crest_pos), 
        dir + "003.png", 
        '#b44c97')

    # sawtooth  crest_pos = 1.0
    wave = SawtoothWave(num_cycles = 3, frequency = 1e6, amplitude = 1000, crest_pos = 1.0)
    plot_graph(
        sampling_rate,
        wave.gen_samples(sampling_rate), 
        "sawtooth [cycles:{}, freq:{} [MHz], amp:{}, phase:{}, offset:{}, crest pos:{}]"
        .format(wave.num_cycles, wave.frequency/1e6, wave.amplitude, to_degree(wave.phase), wave.offset, wave.crest_pos), 
        dir + "004.png", 
        '#b44c97')

    # square  duty = 0.5
    wave = SquareWave(num_cycles = 2, frequency = 2e6, amplitude = 1000, duty_cycle = 0.5)
    plot_graph(
        sampling_rate,
        wave.gen_samples(sampling_rate), 
        "square [cycles:{}, freq:{} [MHz], amp:{}, phase:{}, offset:{}, duty cycle:{}]"
        .format(wave.num_cycles, wave.frequency/1e6, wave.amplitude, to_degree(wave.phase), wave.offset, wave.duty_cycle), 
        dir + "005.png", 
        '#b44c97')

    # square  duty = 0.8, offset = 1000
    wave = SquareWave(num_cycles = 2, frequency = 2e6, amplitude = 1000, offset = 1000, duty_cycle = 0.8)
    plot_graph(
        sampling_rate,
        wave.gen_samples(sampling_rate), 
        "square [cycles:{}, freq:{} [MHz], amp:{}, phase:{}, offset:{}, duty cycle:{}]"
        .format(wave.num_cycles, wave.frequency/1e6, wave.amplitude, to_degree(wave.phase), wave.offset, wave.duty_cycle), 
        dir + "006.png", 
        '#b44c97')


    # gaussian  duration = 10.0, variance = 2.0
    wave = GaussianPulse(num_cycles = 2, frequency = 4e6, amplitude = 2000, duration = 10.0, variance = 2.0)
    plot_graph(
        sampling_rate,
        wave.gen_samples(sampling_rate), 
        "gaussian [cycles:{}, freq:{} [MHz], amp:{}, phase:{}, offset:{}, dur:{}, var:{}]"
        .format(wave.num_cycles, wave.frequency/1e6, wave.amplitude, to_degree(wave.phase), wave.offset, wave.duration, wave.variance), 
        dir + "007.png", 
        '#b44c97')

    # gaussian  duration = 5.0, variance = 0.1
    wave = GaussianPulse(num_cycles = 3, frequency = 3e6, amplitude = 1000, duration = 5.0, variance = 0.1)
    plot_graph(
        sampling_rate,
        wave.gen_samples(sampling_rate), 
        "gaussian [cycles:{}, freq:{} [MHz], amp:{}, phase:{}, offset:{}, dur:{}, var:{}]"
        .format(wave.num_cycles, wave.frequency/1e6, wave.amplitude, to_degree(wave.phase), wave.offset, wave.duration, wave.variance), 
        dir + "008.png", 
        '#b44c97')
