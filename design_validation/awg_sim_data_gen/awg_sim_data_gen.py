import os
import argparse
import random
import config
from e7awgsw import WaveSequence
from e7awgsw import WAVE_RAM_WORD_SIZE, NUM_SAMPLES_IN_AWG_WORD
from e7awgsw import WaveParamRegs

SAMPLE_START_ADDR = 0 # メモリに格納されたサンプルデータの先頭アドレス

class SampleGenerator(object):

    def __init__(self, cycle):
        self.__idx = 0
        self.__cycle = cycle
        self.__samples = [
            (random.randint(-32768, 32767), random.randint(-32768, 32767))
            for _ in range(self.__cycle)]

    def get(self):
        val = self.__samples[self.__idx]
        self.__idx += 1
        if self.__idx == self.__cycle:
            self.__idx = 0

        return val
        
    def get_list(self, num):
        return [self.get() for _ in range(num)]


def gen_wave_seq(use_max):
    """ config モジュールの設定に従って波形シーケンスを作る """
    ulimit = config.upper_limit
    if use_max:
        num_wait_words = ulimit['num_wait_words']
        num_seq_repeats = ulimit['num_seq_repeats']
        num_chunks = ulimit['num_chunks']
        num_chunk_repeats_list = ulimit['num_chunk_repeats_list'][:num_chunks]
        num_wave_words_list = ulimit['num_wave_words_list'][:num_chunks]
        num_post_blank_words_list = ulimit['num_post_blank_words_list'][:num_chunks]
    else:
        num_wait_words = random.randint(0, ulimit['num_wait_words'])
        num_seq_repeats = random.randint(1, ulimit['num_seq_repeats'])
        num_chunks = random.randint(1, ulimit['num_chunks'])
        num_chunk_repeats_list = [
            random.randint(1, max_repeats)
            for max_repeats in ulimit['num_chunk_repeats_list'][:num_chunks]]
        num_wave_words_list = [
            random.randint(1, (max_wave_words + 15) // 16) * 16
            for max_wave_words in ulimit['num_wave_words_list'][:num_chunks]]
        num_post_blank_words_list = [
            random.randint(1, max_post_blank_words)
            for max_post_blank_words in ulimit['num_post_blank_words_list'][:num_chunks]]

    wave_seq = WaveSequence(num_wait_words, num_seq_repeats)
    sample_gen = SampleGenerator(32768)
    for i in range(num_chunks):
        wave_seq.add_chunk(
            iq_samples = sample_gen.get_list(num_wave_words_list[i] * 4),
            num_blank_words = num_post_blank_words_list[i],
            num_repeats = num_chunk_repeats_list[i])
    
    return wave_seq


def gen_sample_byte_data(wave_seq):
    """ 波形シーケンスを構成するサンプルのバイトデータを作成する """
    byte_data = bytearray()
    for chunk in wave_seq.chunk_list:
        wave_bytes = chunk.wave_data.serialize()
        rem = len(wave_bytes) % WAVE_RAM_WORD_SIZE
        if rem != 0:
            wave_bytes += bytearray([0] * (WAVE_RAM_WORD_SIZE - rem))
        byte_data += wave_bytes
    
    return byte_data
        

def output_sample_mem_img(sample_bytes, file_path):
    """ 波形シーケンスを構成するサンプルデータを格納したメモリイメージを出力する """
    with open(file_path, 'w') as txt_file:
        for i in range(0, len(sample_bytes), WAVE_RAM_WORD_SIZE):
            for j in reversed(range(WAVE_RAM_WORD_SIZE)):
                txt_file.write('{:02X}'.format(sample_bytes[i + j]))
            txt_file.write('\n')


def calc_chunk_addr(wave_seq):
    addr_list = []
    addr = SAMPLE_START_ADDR
    for chunk in wave_seq.chunk_list:
        addr_list.append(addr)
        addr += (chunk.wave_data.num_bytes + WAVE_RAM_WORD_SIZE  - 1) \
                 // WAVE_RAM_WORD_SIZE * WAVE_RAM_WORD_SIZE

    return addr_list


def output_wave_params(wave_seq, file_path):
    """ 波形パラメータを出力する """
    addr_list = calc_chunk_addr(wave_seq)
    with open(file_path, 'w') as txt_file:
        offset = WaveParamRegs.Offset
        txt_file.write('{:04X} {:08X}\n'.format(offset.NUM_WAIT_WORDS, wave_seq.num_wait_words))
        txt_file.write('{:04X} {:08X}\n'.format(offset.NUM_REPEATS, wave_seq.num_repeats))
        txt_file.write('{:04X} {:08X}\n'.format(offset.NUM_CHUNKS, wave_seq.num_chunks))
        for i in range(wave_seq.num_chunks):
            chunk = wave_seq.chunk(i)
            param_addr = offset.chunk(i) + offset.CHUNK_START_ADDR
            txt_file.write('{:04X} {:08X}\n'.format(param_addr, addr_list[i] // 16))
            param_addr = offset.chunk(i) + offset.NUM_WAVE_PART_WORDS
            txt_file.write('{:04X} {:08X}\n'.format(param_addr, chunk.num_wave_words))
            param_addr = offset.chunk(i) + offset.NUM_BLANK_WORDS
            txt_file.write('{:04X} {:08X}\n'.format(param_addr, chunk.num_blank_words))
            param_addr = offset.chunk(i) + offset.NUM_CHUNK_REPEATS
            txt_file.write('{:04X} {:08X}\n'.format(param_addr, chunk.num_repeats))

    dot_pos = file_path.rfind('.')
    file_path = file_path[:dot_pos] + '_legible' + file_path[dot_pos:]
    with open(file_path, 'w') as txt_file:
        txt_file.write(str(wave_seq))


def output_user_def_wave(wave_seq, file_path):
    """ ユーザ定義波形を出力する """
    with open(file_path, 'w') as txt_file:
        samples = wave_seq.all_samples(True)
        for i in range(0, len(samples), NUM_SAMPLES_IN_AWG_WORD):
            if i % 64 == 0:
                sideband = 1
            elif i % 64 == 60:
                sideband = 2
            else:
                sideband = 0

            awg_word = 0
            for j in range(NUM_SAMPLES_IN_AWG_WORD):
                iq = samples[i + j]
                awg_word |= (0xFFFF & iq[0]) << (j * 32)
                awg_word |= (0xFFFF & iq[1]) << (j * 32 + 16)

            txt_file.write('{}{:032X}\n'.format(sideband, awg_word))


def output_sim_data(data_set_id, use_max):
    dir_path = 'result/{:03d}'.format(data_set_id)
    os.makedirs(dir_path, exist_ok = True)   
    wave_seq = gen_wave_seq(use_max)
    sample_bytes = gen_sample_byte_data(wave_seq)

    file_path = dir_path + '/sample_mem_img.txt'
    output_sample_mem_img(sample_bytes, file_path)
    file_path = dir_path + '/wave_params.txt'
    output_wave_params(wave_seq, file_path)
    file_path = dir_path + '/exp_user_def_wave.txt'
    output_user_def_wave(wave_seq, file_path)


if __name__ == "__main__":
    random.seed(11)
    parser = argparse.ArgumentParser()
    parser.add_argument('--num-data-set', default=1, type=int)
    parser.add_argument('--use-max', action='store_true')
    args = parser.parse_args()
    
    for i in range(args.num_data_set):
        output_sim_data(i, args.use_max)
