from __future__ import annotations

import struct
from typing_extensions import Self
from typing import Any, Final, overload
from collections.abc import Sequence, Iterator
from logging import Logger
from .hwparam import WAVE_SAMPLE_SIZE, AWG_WORD_SIZE, NUM_SAMPLES_IN_AWG_WORD, NUM_SAMPLES_IN_WAVE_BLOCK
from .logger import get_file_logger, get_null_logger, log_error

class WaveSequence(object):
    """ 波形シーケンスの情報を保持するクラス"""

    MAX_POST_BLANK_LEN: Final = 0xFFFFFFFF    #: 最大ポストブランク長
    MAX_CHUNK_REPEATS: Final = 0xFFFFFFFF     #: 波形チャンクの最大リピート回数
    MAX_WAIT_WORDS: Final = 0xFFFFFFFF        #: 波形シーケンスの先頭に付く 0 データの最大の長さ
    MAX_SEQUENCE_REPEATS: Final = 0xFFFFFFFF  #: 波形シーケンスの最大リピート回数
    MAX_CHUNKS: Final = 16                    #: 波形シーケンスに登録可能な最大チャンク数
    NUM_SAMPLES_IN_WAVE_BLOCK: Final = NUM_SAMPLES_IN_WAVE_BLOCK #: 1 波形ブロック当たりのサンプル数
    NUM_SAMPLES_IN_AWG_WORD: Final = NUM_SAMPLES_IN_AWG_WORD #: 1 AWG ワード当たりのサンプル数

    def __init__(
        self,
        num_wait_words: int,
        num_repeats: int,
        *,
        enable_lib_log: bool = True,
        logger: Logger = get_null_logger()
    ) -> None:
        """
        Args:
            num_wait_words (int): 
                | 波形シーケンスの先頭に付く 0 データの長さ.  
                | 1 AWG ワードは 4 サンプル. (I データと Q データはまとめて 1 サンプルとカウント)
            num_repeats (int): 波形シーケンスを繰り返す回数
            enable_lib_log (bool):
                | True -> ライブラリの標準のログ機能を有効にする.
                | False -> ライブラリの標準のログ機能を無効にする.
            logger (logging.Logger): ユーザ独自のログ出力に用いる Logger オブジェクト
        """
        self.__loggers = [logger]
        if enable_lib_log:
            self.__loggers.append(get_file_logger())

        try:
            if not (isinstance(num_wait_words, int) and 
                    (0 <= num_wait_words and num_wait_words <= self.MAX_WAIT_WORDS)):
                raise ValueError(
                    "The number of wait words must be an integer between {} and {} inclusive.  '{}' was set."
                    .format(0, self.MAX_WAIT_WORDS, num_repeats))

            if not (isinstance(num_repeats, int) and 
                    (1 <= num_repeats and num_repeats <= self.MAX_SEQUENCE_REPEATS)):
                raise ValueError(
                    "The number of times to repeat a wave sequence must be an integer between {} and {} inclusive.  '{}' was set."
                    .format(1, self.MAX_SEQUENCE_REPEATS, num_repeats))
        except Exception as e:
            log_error(e, *self.__loggers)
            raise

        self.__chunks: list[WaveChunk] = []
        self.__num_wait_words = num_wait_words
        self.__num_repeats = num_repeats

    def del_chunk(self, index: int) -> None:
        if index < len(self.__chunks):
            del self.__chunks[index]
        
    def add_chunk(
        self,
        iq_samples: Sequence[tuple[int, int]],
        num_blank_words: int,
        num_repeats: int
    ) -> None:
        """波形チャンクを追加する

        Args:
            iq_samples (Sequence of (int, int)):
                | 各サンプルの I データと Q データを格納したタプルのシーケンス.
                | タプルの 0 番目に I データを格納して 1 番目に Q データを格納する.
                | シーケンスの要素数は送信波形の 1 ブロックに含まれるサンプル数 (= 64) の倍数でなければならない.
                | タプルの各要素は 2bytes で表せる整数値でなければならない. (符号付, 符号なしは問わない)
            num_blank_words (int): 
                | 追加する波形チャンク内で iq_samples に続く 0 データ (ポストブランク) の長さ.
                | 単位は AWG ワード.
                | 1 AWG ワードは 4 サンプル. (I データと Q データはまとめて 1 サンプルとカウント)
            num_repeats (int): 追加する波形チャンクを繰り返す回数
        """
        try:
            if not isinstance(iq_samples, Sequence):
                raise ValueError('Invalid sample list  ({})'.format(iq_samples))
            
            if (len(self.__chunks) == self.MAX_CHUNKS):
                raise ValueError("No more wave chunks can be added. (max=" + str(self.MAX_CHUNKS) + ")")
            
            num_samples = len(iq_samples)
            if num_samples == 0:
                raise ValueError('Empty sample list was set.')

            if num_samples % NUM_SAMPLES_IN_WAVE_BLOCK != 0:
                raise ValueError(
                    'The number of samples in a wave chunk must be a multiple of {}.  ({} was set.)'
                    .format(NUM_SAMPLES_IN_WAVE_BLOCK, num_samples))

            try:
                # 2 bytes で表せる数かどうかチェック
                for iq_sample in iq_samples:
                    if len(iq_sample) != 2:
                        raise Exception
                    for sample in iq_sample:
                        if not self.__is_in_range(-32768, 0xFFFF, sample):
                            raise Exception
            except:
                raise ValueError(
                    "An AWG sample value must be a pair of integers that can be expressed in 2 bytes.  (err val = '{}')"
                    .format(iq_sample))

            if not (isinstance(num_blank_words, int) and 
                    (0 <= num_blank_words and num_blank_words <= self.MAX_POST_BLANK_LEN)):
                raise ValueError(
                    "Post blank length must be an integer between {} and {} inclusive.  '{}' was set."
                    .format(0, self.MAX_POST_BLANK_LEN, num_blank_words))

            if not (isinstance(num_repeats, int) and 
                    (1 <= num_repeats and num_repeats <= self.MAX_CHUNK_REPEATS)):
                raise ValueError(
                    "The number of times to repeat a wave chunk must be an integer between {} and {} inclusive.  '{}' was set."
                    .format(1, self.MAX_CHUNK_REPEATS, num_repeats))
        except Exception as e:
            log_error(e, *self.__loggers)
            raise

        self.__chunks.append(WaveChunk(iq_samples, num_blank_words, num_repeats))

    @property
    def num_chunks(self) -> int:
        """現在登録されている波形チャンクの数
        
        Returns:
            int: 登録されているチャンク数
        """
        return len(self.__chunks)

    def chunk(self, idx: int) -> WaveChunk:
        """引数で指定した番号の波形チャンクを返す
        
        Args:
            idx: 取得する波形チャンクの番号 (登録順)

        Returns:
            WaveChunk: 引数で指定した波形チャンク
        """
        return self.__chunks[idx]

    @property
    def chunk_list(self) -> list[WaveChunk]:
        """現在登録されている波形チャンクのリスト

        Returns:
            list of WaveChunk: 現在登録されている波形チャンクのリスト
        """
        return list(self.__chunks)

    @property
    def num_wait_samples(self) -> int:
        """波形シーケンスの先頭に付く 0 データのサンプル数.

        Returns:
            int: 波形シーケンスの先頭に付く 0 データのサンプル数.
        """
        return self.num_wait_words * NUM_SAMPLES_IN_AWG_WORD

    @property
    def num_wait_words(self) -> int:
        """波形シーケンスの先頭に付く 0 データの長さ.
        
        | 単位は AWG ワード.
        | 1 AWG ワードは 4 サンプル. (I データと Q データはまとめて 1 サンプルとカウント)

        Returns:
            int: 波形シーケンスの先頭に付く 0 データの長さ
        """
        return self.__num_wait_words

    @property
    def num_repeats(self) -> int:
        """波形シーケンスを繰り返す回数

        Returns:
            int: 波形シーケンスを繰り返す回数
        """
        return self.__num_repeats

    @num_repeats.setter
    def num_repeats(self, value: int) -> None:
        """波形シーケンスを繰り返す回数

        Args:
            *value (int)
        """
        self.__num_repeats = value

    @property
    def num_all_samples(self) -> int:
        """この波形シーケンスの全サンプル数 (繰り返しも含む)

        Returns:
            int: この波形シーケンスの全サンプル数
        """
        return self.num_all_words * NUM_SAMPLES_IN_AWG_WORD

    @property
    def num_all_words(self) -> int:
        """この波形シーケンスの全AWG ワード数 (wait words も繰り返しも含む)
        
        Returns:
            int: この波形シーケンスの全 AWG ワード数
        """
        num_chunk_words = 0
        for chunk in self.__chunks:
            num_chunk_words += chunk.num_words * chunk.num_repeats
        return num_chunk_words * self.__num_repeats + self.__num_wait_words

    def all_samples_lazy(self, include_wait_words: bool = True) -> Sequence[tuple[int, int]]:
        """この波形シーケンスに含まれる全波形サンプルを返す (繰り返しも含む)

        | all_samples の遅延評価版

        Args:
            *include_wait_words (bool)
                | True  -> 戻り値の中にシーケンスの先頭の 0 データを含む
                | False -> 戻り値の中にシーケンスの先頭の 0 データを含まない
        
        Returns:
            Sequence of (int, int): 波形サンプルデータのリスト.
        """
        return self.__WaveSampleList(self, include_wait_words, *self.__loggers)

    def all_samples(self, include_wait_words: bool = True) -> list[tuple[int, int]]:
        """この波形シーケンスに含まれる全波形サンプルを返す (繰り返しも含む)

        Args:
            *include_wait_words (bool)
                | True  -> 戻り値の中にシーケンスの先頭の 0 データを含む
                | False -> 戻り値の中にシーケンスの先頭の 0 データを含まない
        
        Returns:
            list of (int, int): 波形サンプルデータのリスト.
        """
        samples = []
        for chunk in self.__chunks:
            chunk_samples = []
            chunk_samples.extend(chunk.wave_data.samples)
            chunk_samples.extend([(0, 0)] * chunk.num_blank_samples)
            samples.extend(chunk_samples * chunk.num_repeats)
        samples = samples * self.__num_repeats
        
        if include_wait_words:
            return  [(0, 0)] * self.num_wait_samples + samples
                
        return samples

    def save_as_text(self, filepath: str, to_hex: bool = False) -> None:
        """この波形シーケンスをテキストデータとして保存する

        Args:
            filepath (string): 保存するファイルのパス
            to_hex (bool):
                | True -> 16進数として保存
                | False -> 10進数として保存
        """
        try:
            with open(filepath, 'w') as txt_file:
                first_zeros = '0\n' * (self.__num_wait_words * NUM_SAMPLES_IN_AWG_WORD)
                txt_file.write(first_zeros)
                for _ in range(self.__num_repeats):
                    for chunk in self.__chunks:
                        for _ in range(chunk.num_repeats):
                            for i_data, q_data in chunk.wave_data.samples:
                                if to_hex:
                                    i_data = i_data & ((1 << (WAVE_SAMPLE_SIZE // 2 * 8)) - 1)
                                    q_data = q_data & ((1 << (WAVE_SAMPLE_SIZE // 2 * 8)) - 1)
                                    txt_file.write('{:04x}, {:04x}\n'.format(i_data, q_data))
                                else:
                                    txt_file.write('{:7d}, {:7d}\n'.format(i_data, q_data))
                            if to_hex:
                                post_chunk_zeros = '{:04x}, {:04x}\n'.format(0, 0) * (chunk.num_blank_words * NUM_SAMPLES_IN_AWG_WORD)
                            else:
                                post_chunk_zeros = '{:7d}, {:7d}\n'.format(0, 0) * (chunk.num_blank_words * NUM_SAMPLES_IN_AWG_WORD)
                            txt_file.write(post_chunk_zeros)
        except Exception as e:
            log_error(e, *self.__loggers)
            raise

    def __str__(self) -> str:
        ret = ('num wait words : {}\n'.format(self.__num_wait_words) +
               'num sequence repeats : {}\n'.format(self.__num_repeats) +
               'num chunks : {}\n'.format(self.num_chunks) +
               'num all samples : {}\n\n'.format(self.num_all_samples))
        
        for i in range(self.num_chunks):
            tmp = ('chunk {}\n'.format(i) +
                   '    num wave samples : {}\n'.format(self.chunk(i).wave_data.num_samples) +
                   '    num blank words : {}\n'.format(self.chunk(i).num_blank_words) +
                   '    num repeats : {}\n'.format(self.chunk(i).num_repeats))
            ret += tmp
        return ret + "\n"

    def __is_in_range(self, min: int, max: int, val: int) -> bool:
        return (min <= val) and (val <= max)


    class __WaveSampleList(Sequence[tuple[int, int]]):

        def __init__(
            self,
            wave_seq: WaveSequence,
            include_wait_words: bool,
            *loggers: Logger
        ) -> None:
            self.__chunks = wave_seq.chunk_list
            if include_wait_words:
                self.__num_wait_samples = wave_seq.num_wait_words * NUM_SAMPLES_IN_AWG_WORD
                self.__len = wave_seq.num_all_samples
            else:
                self.__num_wait_samples = 0
                self.__len = wave_seq.num_all_samples - wave_seq.num_wait_samples

            self.__chunk_range_list = self.__gen_chunk_range_list(self.__chunks)

            # 1 波形シーケンス当たりのサンプル数
            self.__num_samples_in_seq = (self.__len - self.__num_wait_samples) // wave_seq.num_repeats
            self.__loggers = loggers
        
        def __gen_chunk_range_list(self, chunks: Sequence[WaveChunk]) -> list[tuple[int, int]]:
            chunk_range_list = []
            start_idx = 0
            for chunk in chunks:
                end_idx = start_idx + chunk.num_repeats * chunk.num_samples - 1
                chunk_range_list.append((start_idx, end_idx))
                start_idx = end_idx + 1
            return chunk_range_list

        def __repr__(self) -> str:
            return self.__str__()

        def __str__(self) -> str:
            len = min(self.__len, 12)
            items = []
            for i in range(len):
                items.append(str(self[i]))
            if self.__len > 12:
                items.append('...')
            return '[' + ', '.join(items) + ']'

        def __iter__(self) -> Iterator[tuple[int, int]]:
            return self.WaveIter(self)

        @overload
        def __getitem__(self, index: int) -> tuple[int, int]: ...

        @overload
        def __getitem__(self, index: slice) -> list[tuple[int, int]]: ...

        def __getitem__(self, key: int | slice) -> tuple[int, int] | list[tuple[int, int]]:
            if isinstance(key, int):
                return self.get(key)
            elif isinstance(key, slice):
                return [self.get(i) for i in range(*key.indices(self.__len))]
            else:
                msg = 'Invalid argument type.'
                log_error(msg, *self.__loggers)
                raise TypeError(msg)

        def get(self, key: int) -> tuple[int, int]:
            if key < 0:
                    key += self.__len
            if (key < 0) or (self.__len <= key):
                msg = 'The index [{}] is out of range.'.format(key)
                log_error(msg, *self.__loggers)
                raise IndexError(msg)
            if key < self.__num_wait_samples:
                return (0, 0)

            key = (key - self.__num_wait_samples) % self.__num_samples_in_seq
            chunk, start_idx, _ = self.__find_chunk(key)
            key = (key - start_idx) % chunk.num_samples
            if key < chunk.wave_data.num_samples:
                return chunk.wave_data.sample(key)
            else:
                return (0, 0)

        def __find_chunk(self, idx: int) -> tuple[WaveChunk, int, int]:
            first = 0
            last = len(self.__chunk_range_list) - 1
            while first <= last:
                target = (first + last) // 2
                start, end = self.__chunk_range_list[target]
                if (start <= idx) and (idx <= end):
                    return (self.__chunks[target], start, end)
                if end < idx:
                    first = target + 1
                else:
                    last = target - 1

            assert False, ('unreachable')

        def __len__(self) -> int:
            return self.__len

        def __contains__(self, item: object) -> bool:
            if (self.__num_wait_samples > 0) and item == (0, 0):
                return True

            for chunk in self.__chunks:
                if (chunk.num_blank_samples > 0) and item == (0, 0):
                    return True
                for sample in chunk.wave_data.samples:
                    if item == sample:
                        return True

            return False

        def __eq__(self, other: Any) -> bool:
            try:
                if self is other:
                    return True
                                                
                if (other is None) or (len(self) != len(other)):
                    return False
                
                for i in range(len(self)):
                    if self[i] != other[i]:
                        return False

                return True
            except:
                return NotImplemented
        
        def __ne__(self, other: object):
            return not self == other


        class WaveIter(Iterator[tuple[int, int]]):

            def __init__(self, outer: WaveSequence.__WaveSampleList) -> None:
                self._i = 0
                self.__outer = outer

            def __iter__(self) -> Self:
                return self

            def __next__(self) -> tuple[int, int]:
                if self._i == len(self.__outer):
                    raise StopIteration()
                val = self.__outer.get(self._i)
                self._i += 1
                return val


class WaveChunk(object):
    """波形チャンクの情報を保持するクラス"""

    def __init__(
        self,
        samples: Sequence[tuple[int, int]],
        num_blank_words: int,
        num_repeats: int
    ) -> None:
        self.__wave_data = WaveData(samples, WAVE_SAMPLE_SIZE)
        self.__num_blank_words = num_blank_words
        self.__num_repeats = num_repeats

    @property
    def wave_data(self) -> WaveData:
        """この波形チャンクのポストブランクを除く波形データ

        Returns:
            WaveData: この波形チャンクのポストブランクを除く波形データ
        """
        return self.__wave_data

    @property
    def num_blank_words(self) -> int:
        """この波形チャンクのポストブランクの長さ
        
        Returns:
            int: 
                | この波形チャンクのポストブランクの長さ.
                | 単位は AWG ワード.
                | 1 AWG ワードは 4 サンプル. (I データと Q データはまとめて 1 サンプルとカウント)
        """
        return self.__num_blank_words

    @property
    def num_blank_samples(self) -> int:
        """この波形チャンクのポストブランクのサンプル数
        
        Returns:
            int: この波形チャンクのポストブランクのサンプル数
        """
        return self.num_blank_words * NUM_SAMPLES_IN_AWG_WORD

    @property
    def num_wave_words(self) -> int:
        """この波形チャンクの有波形部の長さ
        
        Returns:
            int: 
                | この波形チャンクの有波形部の長さ
                | 単位は AWG ワード.
                | 1 AWG ワードは 4 サンプル. (I データと Q データはまとめて 1 サンプルとカウント)
        """
        return self.__wave_data.num_bytes // AWG_WORD_SIZE

    @property
    def num_wave_samples(self) -> int:
        """この波形チャンクの有波形部のサンプル数
        
        Returns:
            int: この波形チャンクの有波形部のサンプル数
        """
        return self.num_wave_words * NUM_SAMPLES_IN_AWG_WORD

    @property
    def num_repeats(self) -> int:
        """この波形チャンクを繰り返す回数
        
        Returns:
            int: この波形チャンクを繰り返す回数
        """
        return self.__num_repeats

    @property
    def num_words(self) -> int:
        """この波形チャンクのワード数.

        1 AWG ワードは 4 サンプル. (I データと Q データはまとめて 1 サンプルとカウント)
        
        Returns:
            int: この波形チャンクのワード数
        """
        return self.num_wave_words + self.num_blank_words

    @property
    def num_samples(self) -> int:
        """この波形チャンクのサンプル数.

        Returns:
            int: この波形チャンクのサンプル数
        """
        return self.num_words * NUM_SAMPLES_IN_AWG_WORD


class WaveData(object):
    """波形のサンプルデータを保持するクラス"""

    def __init__(self, samples: Sequence[tuple[int, int]], wave_sample_size: int) -> None:
        self.__samples = list(samples)
        self.__wave_sample_size = wave_sample_size

    @property
    def samples(self) -> list[tuple[int, int]]:
        """波形データのサンプルリスト

        Returns:
            list of int: 波形データのサンプルリスト
        """
        return list(self.__samples)

    def sample(self, idx: int) -> tuple[int, int]:
        """引数で指定したサンプルを返す
        
        Rturns:
            (int, int): サンプル値のタプル (I データ, Q データ)
        """
        return self.__samples[idx]

    @property
    def num_samples(self) -> int:
        """波形データのサンプル数
        
        Returns:
            int: 波形データのサンプル数
        """
        return len(self.__samples)

    @property
    def num_bytes(self) -> int:
        """波形データのバイト数
        
        Returns:
            int: 波形データのバイト数
        """
        return len(self.__samples) * self.__wave_sample_size

    def serialize(self) -> bytes:
        payload = bytearray()
        for i_data, q_data in self.__samples:
            i_data = i_data & ((1 << (self.__wave_sample_size // 2 * 8)) - 1)
            q_data = q_data & ((1 << (self.__wave_sample_size // 2 * 8)) - 1)
            payload += struct.pack('<H', i_data)
            payload += struct.pack('<H', q_data)
        return payload

    @classmethod
    def deserialize(cls, data: bytes, wave_sample_size: int) -> WaveData:
        samples = []
        num_samples = len(data) // wave_sample_size
        for i in range(num_samples):
            iq_data = int.from_bytes(data[i * wave_sample_size : (i + 1) * wave_sample_size], 'little')
            mask = ((1 << (wave_sample_size // 2 * 8)) - 1)
            minval = 1 << (wave_sample_size // 2 * 8 - 1)
            i_data = iq_data & mask
            i_data = (i_data ^ minval) - minval
            q_data = (iq_data >> (wave_sample_size // 2 * 8)) & mask
            q_data = (q_data ^ minval) - minval
            samples.append((i_data, q_data))

        return WaveData(samples, wave_sample_size)
