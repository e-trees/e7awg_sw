from abc import ABCMeta, abstractmethod
from collections.abc import Sequence
import math

class ParameterizedWave(object, metaclass = ABCMeta):
    """パラメータで表される波形のベースクラス"""
    def __init__(
        self,
        num_cycles: float,
        frequency: float,
        amplitude: float,
        phase: float,
        offset: float
    ) -> None:
        """
        Args:
            num_cycles (int or float): サイクル数
            frequency (int or float): 周波数 (単位: Hz)
            amplitude (int or float): 振幅
            phase (int or float): 位相 (単位: radian)
            offset (int or float): 振幅オフセット
        """
        if not (isinstance(num_cycles, (int, float)) and num_cycles > 0):
            raise ValueError("The 'num_cycles' must be a number greater than zero.  ({})".format(num_cycles))

        if not (isinstance(frequency, (int, float)) and frequency >= 0):
            raise ValueError("The 'frequency' must be a number greater than zero.  ({})".format(frequency))
        
        if not isinstance(phase, (int, float)):
            raise ValueError("The 'phase' must be a number.  ({})".format(phase))

        if not isinstance(amplitude, (int, float)):
            raise ValueError("The 'amplitude' must be a number.  ({})".format(amplitude))

        if not isinstance(offset, (int, float)):
            raise ValueError("The 'offset' must be a number.  ({})".format(offset))

        self.__num_cycles = num_cycles
        self.__frequency = frequency
        self.__phase = phase
        self.__amplitude = amplitude
        self.__offset = offset

    @property
    def num_cycles(self) -> float:
        """サイクル数
        
        Returns:
            int or float: サイクル数
        """
        return self.__num_cycles

    @property
    def frequency(self) -> float:
        """周波数 (単位: Hz)

        Returns:
            int or float: 周波数
        """
        return self.__frequency

    @property
    def phase(self) -> float:
        """位相 (単位: radian)
        
        Returns:
            int or float: 位相
        """
        return self.__phase

    @property
    def amplitude(self) -> float:
        """振幅

        Returns:
            int or float: 振幅
        """
        return self.__amplitude

    @property
    def offset(self) -> float:
        """振幅オフセット
        
        Returns:
            int or float: 振幅オフセット
        """
        return self.__offset

    @abstractmethod
    def gen_samples(self, sampling_rate: float) -> list[int]:
        pass


class SinWave(ParameterizedWave):
    """正弦波クラス"""

    def __init__(
        self,
        num_cycles: float,
        frequency: float,
        amplitude: float,
        *,
        phase: float = 0.0,
        offset: float = 0.0
    ) -> None:
        """
        Args:
            num_cycles (int or float): サイクル数
            frequency (int or float): 周波数 (単位: Hz)
            amplitude (int or float): 振幅
            phase (int or float): 位相 (単位: radian)
            offset (int or float): 振幅オフセット
        """
        super().__init__(num_cycles, frequency, amplitude, phase, offset)

    def gen_samples(self, sampling_rate: float) -> list[int]:
        """このオブジェクトのパラメータに従う sin 波のサンプルリストを生成する

        Args:
            sampling_rate (int or float): サンプリングレート (単位: サンプル数/秒)
        
        Returns:
            list of int: sin 波のサンプルリスト
        """
        if not isinstance(sampling_rate, (int, float)):
            raise ValueError(
                "The 'sampling_rate' must be a number greater than zero.  ({})".format(sampling_rate))

        num_samples = int(sampling_rate * self.num_cycles / self.frequency)
        ang_freq = 2 * math.pi * self.frequency
        return [int(self.amplitude * math.sin(ang_freq * i / sampling_rate + self.phase) + self.offset)
                for i in range(num_samples)]


class SawtoothWave(ParameterizedWave):
    """ノコギリ波クラス"""

    def __init__(
        self,
        num_cycles: float,
        frequency: float,
        amplitude: float,
        *,
        phase: float = 0.0,
        offset: float = 0.0,
        crest_pos: float = 1.0
    ) -> None:
        """
        Args:
            num_cycles (int or float): サイクル数
            frequency (int or float): 周波数 (単位: Hz)
            amplitude (int or float): 振幅
            phase (int or float): 位相 (単位: radian)
            offset (int or float): 振幅オフセット
            crest_pos (int or float): 
                | ノコギリ波の頂点の位置. (0.0 ~ 1.0)
                | 0 のとき, 各サイクルの先頭に頂点がくるような波となる.
                | 1 のとき, 各サイクルの末尾に頂点がくるような波となる.
        """
        if not (isinstance(crest_pos, (int, float)) and 
                (0 <= crest_pos and crest_pos <= 1)):
            raise ValueError("The 'crest_pos' must be between 0.0 and 1.0 inclusive.  ({})".format(crest_pos))
        
        self.__crest_pos = crest_pos
        super().__init__(num_cycles, frequency, amplitude, phase, offset)

    @property
    def crest_pos(self) -> float:
        """ノコギリ波の頂点の位置

        Returns:
            int or float: ノコギリ波の頂点の位置
        """
        return self.__crest_pos

    def gen_samples(self, sampling_rate: float) -> list[int]:
        """このオブジェクトのパラメータに従うノコギリ波のサンプルリストを生成する
        
        Args:
            sampling_rate (int or float): サンプリングレート (単位: サンプル数/秒)

        Returns:
            list of int: ノコギリ波のサンプルリスト
        """
        if not (isinstance(sampling_rate, (int, float)) and (sampling_rate > 0)):
            raise ValueError(
                "The 'sampling_rate' must be a number greater than zero.  ({})".format(sampling_rate))

        num_samples = int(sampling_rate * self.num_cycles / self.frequency)
        samples = []
        x_offset = self.phase / (2 * math.pi * self.frequency)
        x_crest = self.crest_pos / self.frequency
        x_crest_rev = (1.0 - self.crest_pos) / self.frequency

        for i in range(num_samples):
            x_val = i / sampling_rate + x_offset
            if x_val >= 0:
                x_val = x_val - int(x_val * self.frequency) / self.frequency
            else:
                x_val = math.ceil(-x_val * self.frequency) / self.frequency + x_val

            if (x_val < x_crest) or (self.crest_pos == 1):
                y_val = x_val * (2 * self.amplitude) / x_crest - self.amplitude
            else:
                y_val = -x_val * (2 * self.amplitude) / x_crest_rev \
                        + self.amplitude * (1.0 + self.crest_pos) / (1.0 - self.crest_pos)
            samples.append(int(y_val + self.offset))

        return samples


class SquareWave(ParameterizedWave):
    """方形波クラス"""

    def __init__(
        self,
        num_cycles: float,
        frequency: float,
        amplitude: float,
        *,
        phase: float = 0.0,
        offset: float = 0.0,
        duty_cycle: float = 0.5
    ) -> None:
        """
        Args:
            num_cycles (int or float): サイクル数
            frequency (int or float): 周波数 (単位: Hz)
            amplitude (int or float): 振幅
            phase (int or float): 位相 (単位: radian)
            offset (int or float): 振幅オフセット
            duty_cycle (int or float): デューティ比 (0.0 ~ 1.0)
        """
        if not (isinstance(duty_cycle, (int, float)) and 
                (0 <= duty_cycle and duty_cycle <= 1)):
            raise ValueError("The 'duty_cycle' must be 0.0 ~ 1.0.  ({})".format(duty_cycle))
        
        self.__duty_cycle = duty_cycle
        super().__init__(num_cycles, frequency, amplitude, phase, offset)

    @property
    def duty_cycle(self) -> float:
        """デューティ比
        
        Returns:
            int or float: デューティ比
        """
        return self.__duty_cycle

    def gen_samples(self, sampling_rate: float) -> list[int]:
        """このオブジェクトのパラメータに従う方形波のサンプルリストを生成する
        
        Args:
            sampling_rate (int or float): サンプリングレート (単位: サンプル数/秒)

        Returns:
            list of int: 方形波のサンプルリスト
        """
        if not (isinstance(sampling_rate, (int, float)) and (sampling_rate > 0)):
            raise ValueError(
                "The 'sampling_rate' must be a number greater than zero.  ({})".format(sampling_rate))

        num_samples = int(sampling_rate * self.num_cycles / self.frequency)
        samples = []
        x_offset = self.phase / (2 * math.pi * self.frequency)
        x_border = self.duty_cycle / self.frequency

        for i in range(num_samples):
            x_val = i / sampling_rate + x_offset
            if x_val >= 0:
                x_val = x_val - int(x_val * self.frequency) / self.frequency
            else:
                x_val = math.ceil(-x_val * self.frequency) / self.frequency + x_val

            if (x_val < x_border) or (self.duty_cycle == 1):
                y_val = self.amplitude
            else:
                y_val = -self.amplitude
            samples.append(int(y_val + self.offset))

        return samples


class GaussianPulse(ParameterizedWave):
    """ガウスパルスクラス"""

    def __init__(
        self,
        num_cycles: float,
        frequency: float,
        amplitude: float,
        *,
        phase: float = 0.0,
        offset: float = 0.0,
        duration: float = 2.0,
        variance: float = 1.0
    ) -> None:
        """
        Args:
            num_cycles (int or float): サイクル数
            frequency (int or float): 周波数 (単位: Hz)
            amplitude (int or float): 振幅
            phase (int or float): 位相 (単位: radian)
            offset (int or float): 振幅オフセット
            duration (int or float): 
                | ガウスパルスの長さ.　(0 < duration)
                | ガウス関数の中央が (duration / 2) で左右に (duration / 2) ずつ広がる波形が作られる.
            variance (int or float): ガウスパルスの広がり具合. (0 < variance)
        """
        if not (isinstance(duration, (int, float)) and (0 < duration)):
            raise ValueError("The 'duration' must be a number greater than zero.  ({})".format(duration))
        
        if not (isinstance(variance, (int, float)) and (0 < variance)):
            raise ValueError("The 'variance' must be a number greater than zero.  ({})".format(variance))

        self.__duration = duration
        self.__variance = variance
        super().__init__(num_cycles, frequency, amplitude, phase, offset)

    @property
    def duration(self) -> float:
        """ガウスパルスの長さ

        Returns:
            int or float: ガウスパルスの長さ
        """
        return self.__duration

    @property
    def variance(self) -> float:
        """ガウスパルスの広がり具合

        Returns:
            int or float: ガウスパルスの広がり具合
        """
        return self.__variance

    def gen_samples(self, sampling_rate: float) -> list[int]:
        """このオブジェクトのパラメータに従うガウスパルスのサンプルリストを生成する
        
        Args:
            sampling_rate (int or float): サンプリングレート (単位: サンプル数/秒)

        Returns:
            list of int: ガウスパルスのサンプルリスト
        """
        if not (isinstance(sampling_rate, (int, float)) and (sampling_rate > 0)):
            raise ValueError(
                "The 'sampling_rate' must be a number greater than zero.  ({})".format(sampling_rate))

        num_samples = int(sampling_rate * self.num_cycles / self.frequency)
        samples = []
        x_offset = self.duration * self.phase / (2 * math.pi)
        whole_duration = self.duration * self.num_cycles

        for i in range(num_samples):
            x_val = i * whole_duration / num_samples + x_offset
            if x_val >= 0:
                x_val = x_val - int(x_val / self.duration) * self.duration
            else:
                x_val = math.ceil(-x_val / self.duration) * self.duration + x_val

            tmp = x_val - (self.duration / 2)
            y_val = self.amplitude * math.exp(-0.5 * tmp * tmp / self.variance)
            samples.append(int(y_val + self.offset))

        return samples


class IqWave(object):
    """I/Q 波形クラス"""

    def __init__(self, i_wave: ParameterizedWave, q_wave: ParameterizedWave) -> None:
        """
        Args:
            i_wave (ParameterizedWave): I 相の波形オブジェクト
            q_wave (ParameterizedWave): Q 相の波形オブジェクト
        """
        if not (isinstance(i_wave, ParameterizedWave)):
            raise ValueError("The 'i_wave' must be a ParameterizedWave.")
        if not (isinstance(q_wave, ParameterizedWave)):
            raise ValueError("The 'q_wave' must be a ParameterizedWave.")
        self.__i_wave = i_wave
        self.__q_wave = q_wave

    @classmethod
    def convert_to_iq_format(
        cls,
        i_samples: Sequence[int],
        q_samples: Sequence[int],
        padding_size: int
    ) -> list[tuple[int, int]]:
        """I 相と Q 相のサンプルリストをまとめて I/Q データフォーマットに変換する

        Args:
            i_samples (Sequence of int): I 相のサンプルリスト
            q_samples (Sequence of int): Q 相のサンプルリスト
            padding_size (int): 戻り値の I/Q 波形データのサンプル数が, この値の倍数になるように I/Q サンプルリストに 0 データを追加する.

        Returns:
            list of (int, int): 
                | I 相と Q 相のサンプルのタプルのリスト.
                | タプルの 0 番目に I データが格納され, 1 番目に Q データが格納される.
        """
        if not isinstance(padding_size, int):
            raise ValueError("The 'padding_size' must be an integer.  ({})".format(padding_size))

        iq_samples = list(zip(i_samples, q_samples))
        if len(iq_samples) % padding_size != 0:
            num_samples_to_add = padding_size - (len(iq_samples) % padding_size)
            iq_samples.extend([(0, 0)] * num_samples_to_add)
        return iq_samples

    @property
    def i_wave(self) -> ParameterizedWave:
        """I 相の波形オブジェクト
        
        Returns:
             subclass of ParameterizedWave: I 相の波形オブジェクト
        """
        return self.__i_wave

    @property
    def q_wave(self) -> ParameterizedWave:
        """Q 相の波形オブジェクト
        
        Returns:
             subclass of ParameterizedWave: Q 相の波形オブジェクト
        """
        return self.__q_wave

    def gen_samples(self, sampling_rate: float, padding_size: int = 1) -> list[tuple[int, int]]:
        """I/Q 波形を生成する

        Args:
            sampling_rate (int or float): サンプリングレート (単位: サンプル数/秒)
            padding_size (int): 戻り値の I/Q 波形データのサンプル数が, この値の倍数になるように I/Q サンプルリストに 0 データを追加する.

        Returns:
            list of (int, int): 
                | I 相と Q 相のサンプルのタプルのリスト.
                | タプルの 0 番目に I データが格納され, 1 番目に Q データが格納される.
        """
        if not isinstance(sampling_rate, (int, float)):
            raise ValueError("The 'sampling_rate' must be a number.  ({})".format(sampling_rate))

        if not isinstance(padding_size, int):
            raise ValueError("The 'padding_size' must be an integer.  ({})".format(padding_size))

        i_samples = self.__i_wave.gen_samples(sampling_rate)
        q_samples = self.__q_wave.gen_samples(sampling_rate)
        diff = abs(len(i_samples) - len(q_samples))
        if diff != 0:
            long, short = ('I', 'Q') if len(q_samples) < len(i_samples) else ('Q', 'I')
            print('[WARNING] The length of the {} wave is shorter than the one of the {} wave.  '.format(short, long) +
                  '{} zero sample(s) are added to the end of the {} wave.'.format(diff, short))
        
        if len(i_samples) < len(q_samples):
            i_samples.extend(diff * [0])
        if len(q_samples) < len(i_samples):
            q_samples.extend(diff * [0])        

        for samples in (i_samples, q_samples):
            if len(samples) % padding_size != 0:
                additional_samples = padding_size - (len(samples) % padding_size)
                samples.extend([0] * additional_samples)
        
        return list(zip(i_samples, q_samples))
