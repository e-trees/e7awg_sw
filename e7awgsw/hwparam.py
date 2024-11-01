from typing import Final, cast
from abc import ABCMeta, abstractmethod
from typing_extensions import Self
from .hwdefs import E7AwgHwType

############### 後方互換性維持のために存在しているので使用しないこと. ###############
# AWG から出力するサンプルのサイズ (単位 : bytes,  I = 16 bit,  Q = 16 bit)
WAVE_SAMPLE_SIZE: Final = 4
# AWG から 1 サイクルで出力されるデータのサイズ (単位 : bytes)
AWG_WORD_SIZE: Final = 16
# AWG から 1 サイクルで出力されるデータのサンプル数
NUM_SAMPLES_IN_AWG_WORD: Final = AWG_WORD_SIZE // WAVE_SAMPLE_SIZE
# 1 波形ブロックに含まれるサンプル数
NUM_SAMPLES_IN_WAVE_BLOCK: Final = NUM_SAMPLES_IN_AWG_WORD * 16

# ---- Capture Unit ----
# キャプチャユニットが 1 サイクルで取得するデータのサイズ (単位 : bytes)
ADC_WORD_SIZE: Final = 16
# キャプチャユニットが取得するサンプルのサイズ (単位 : bytes,  I = 16 bit,  Q = 16 bit)
ADC_SAMPLE_SIZE: Final = 4
# キャプチャユニットが 1 サイクルで取得するサンプル数
NUM_SAMPLES_IN_ADC_WORD: Final = ADC_WORD_SIZE // ADC_SAMPLE_SIZE
# メモリに保存されたサンプルのサイズ (単位 : bytes,  I = 32 bit,  Q = 32 bit)
CAPTURED_SAMPLE_SIZE: Final = 8
# メモリに保存された四値化結果のサイズ (単位 : bits)
CLASSIFICATION_RESULT_SIZE: Final = 2
# 1 キャプチャユニットが保存可能なデータサイズ (bytes)
MAX_CAPTURE_SIZE: Final = 256 * 1024 * 1024
# 積算ユニットが保持できる積算値の最大数
MAX_INTEG_VEC_ELEMS: Final = 4096
# キャプチャユニットが波形データを保存するアドレス
CAPTURE_ADDR: Final = [
    0x10000000,  0x30000000,  0x50000000,  0x70000000,
    0x90000000,  0xB0000000,  0xD0000000,  0xF0000000,
    0x150000000, 0x170000000
]
# UDP ポート番号
WAVE_RAM_PORT: Final = 0x4000
AWG_REG_PORT: Final = 0x4001
CAPTURE_REG_PORT: Final = 0x4001
#############################################################################

class AwgParams(object, metaclass = ABCMeta):
    """各種デザインの AWG に関連するパラメータを取得するためのインタフェースを規定するクラス."""

    @classmethod
    def of(cls, design_type: E7AwgHwType) -> Self:
        if design_type == E7AwgHwType.SIMPLE_MULTI:
            return cast(Self, AwgParamsSimpleMulti())
        
        if design_type == E7AwgHwType.KR260:
            return cast(Self, AwgParamsKr260())

        if design_type == E7AwgHwType.ZCU111:
            return cast(Self, AwgParamsZcu111())
        
        raise ValueError('Invalid e7awg_hw type.  ({})'.format(design_type))

    @abstractmethod
    def sample_size(self) -> int:
        """
        AWG から出力するサンプルのサイズ (Bytes)
        AWG が I/Q データを出力する場合は, I と Q をまとめて 1 サンプルと数える.
        """
        pass

    @abstractmethod
    def word_size(self) -> int:
        """
        1 AWG ワード当たりのサイズ (Bytes)
        
        | AWG ワード : AWG が 1 サイクルで出力する波形サンプル群

        """
        pass

    @abstractmethod
    def num_samples_in_word(self) -> int:
        """1 AWG ワード当たりのサンプル数"""
        pass

    @abstractmethod
    def num_sample_in_wave_block(self) -> int:
        """AWG の 1 波形ブロックに含まれるサンプル数"""
        pass

    @abstractmethod
    def smallest_unit_of_wave_len(self) -> int:
        """波形チャンクの波形パート (= ポストブランクではない部分) を構成可能なサンプル数の最小単位"""
        pass

    @abstractmethod
    def sampling_rate(self) -> int:
        """AWG のサンプリングレート (サンプル数 / 秒)"""
        pass

    @abstractmethod
    def udp_port(self) -> int:
        """AWG 制御レジスタにアクセスする際に使用する UDP ポート番号"""
        pass


class AwgParamsSimpleMulti(AwgParams):
    """Simple Multi デザインの AWG のパラメータを保持するクラス"""
    
    def sample_size(self) -> int:
        # I = 16 bits,  Q = 16 bits
        return 4

    def word_size(self) -> int:
        return 16
    
    def num_samples_in_word(self) -> int:
        return self.word_size() // self.sample_size()
    
    def num_sample_in_wave_block(self) -> int:
        return self.num_samples_in_word() * 16

    def smallest_unit_of_wave_len(self) -> int:
        return self.num_sample_in_wave_block()

    def sampling_rate(self) -> int:
        return 500_000_000

    def udp_port(self) -> int:
        return 0x4001


class AwgParamsKr260(AwgParams):
    """KR260 デザインの AWG のパラメータを保持するクラス"""

    def sample_size(self) -> int:
        # Real = 16 bits
        return 2

    def word_size(self) -> int:
        return 2
    
    def num_samples_in_word(self) -> int:
        return self.word_size() // self.sample_size()
    
    def num_sample_in_wave_block(self) -> int:
        return self.num_samples_in_word() * 16

    def smallest_unit_of_wave_len(self) -> int:
        return 128

    def sampling_rate(self) -> int:
        return 50_000_000

    def udp_port(self) -> int:
        return 0x4001


class AwgParamsZcu111(AwgParams):
    """ZCU111 デザインの AWG のパラメータを保持するクラス"""

    def sample_size(self) -> int:
        # I = 16 bits,  Q = 16 bits
        return 4

    def word_size(self) -> int:
        return 32
    
    def num_samples_in_word(self) -> int:
        return self.word_size() // self.sample_size()
    
    def num_sample_in_wave_block(self) -> int:
        return self.num_samples_in_word() * 16

    def smallest_unit_of_wave_len(self) -> int:
        return 512

    def sampling_rate(self) -> int:
        return 552_960_000

    def udp_port(self) -> int:
        return 0x4001


class WaveRamParams(object, metaclass = ABCMeta):
    """各種デザインの波形データ RAM のパラメータを取得するためのインタフェースを規定するクラス."""

    @classmethod
    def of(self, design_type: E7AwgHwType) -> Self:
        if design_type == E7AwgHwType.SIMPLE_MULTI:
            return cast(Self, WaveRamParamsSimpleMulti())
        
        if design_type == E7AwgHwType.KR260:
            return cast(Self, WaveRamParamsKr260())

        if design_type == E7AwgHwType.ZCU111:
            return cast(Self, WaveRamParamsZcu111())
        
        raise ValueError('Invalid e7awg_hw type.  ({})'.format(design_type))

    @abstractmethod
    def word_size(self) -> int:
        """波形データ RAM のワードサイズ (Bytes)"""
        pass

    @abstractmethod
    def wave_data_addr(self, awg_id: int) -> int:
        """
        引数で指定した AWG の波形データを格納する波形 RAM のアドレスを返す
        
        | wave_data_addr(n) = AWG n の波形データ格納先アドレス

        """
        pass

    @abstractmethod
    def max_size_for_wave_seq(self) -> int:
        """ 1 波形シーケンスのサンプルデータに割り当てられる最大 RAM サイズ (Bytes)"""
        pass

    @abstractmethod
    def udp_port(self) -> int:
        """波形データ RAM にアクセスする際に使用する UDP ポート番号"""
        pass
        

class WaveRamParamsSimpleMulti(WaveRamParams):
    """Simple Multi デザインの波形データ RAM のパラメータを保持するクラス"""

    def __init__(self) -> None:
        self.__wave_src_addrs: Final = [
            0x0,           0x0_2000_0000, 0x0_4000_0000, 0x0_6000_0000,
            0x0_8000_0000, 0x0_A000_0000, 0x0_C000_0000, 0x0_E000_0000,
            0x1_0000_0000, 0x1_2000_0000, 0x1_4000_0000, 0x1_6000_0000, 
            0x1_8000_0000, 0x1_A0000000,  0x1_C000_0000, 0x1_E000_0000
        ]

    def word_size(self) -> int:
        return 32

    def wave_data_addr(self, awg_id: int) -> int:
        return self.__wave_src_addrs[awg_id]

    def max_size_for_wave_seq(self) -> int:
        return 256 * 1024 * 1024

    def udp_port(self) -> int:
        return 0x4000


class WaveRamParamsKr260(WaveRamParams):
    """KR260 デザインの波形データ RAM のパラメータを保持するクラス"""

    def __init__(self) -> None:
        self.__wave_src_addrs: Final = [
            0x8_0000_0000, 0x8_0400_0000, 0x8_0800_0000, 0x8_0C00_0000,
            0x8_1000_0000, 0x8_1400_0000, 0x8_1800_0000, 0x8_1C00_0000,
            0x8_2000_0000, 0x8_2400_0000, 0x8_2800_0000, 0x8_2C00_0000,
            0x8_3000_0000, 0x8_3400_0000, 0x8_3800_0000, 0x8_3C00_0000
        ]

    def word_size(self) -> int:
        return 16

    def wave_data_addr(self, awg_id: int) -> int:
        return self.__wave_src_addrs[awg_id]

    def max_size_for_wave_seq(self) -> int:
        return 64 * 1024 * 1024

    def udp_port(self) -> int:
        return 0x4000


class WaveRamParamsZcu111(WaveRamParams):
    """ZCU111 デザインの波形データ RAM のパラメータを保持するクラス"""

    def __init__(self) -> None:
        self.__wave_src_addrs: Final = [
            0x0,           0x0_2000_0000, 0x0_4000_0000, 0x0_6000_0000,
            0x0_8000_0000, 0x0_A000_0000, 0x0_C000_0000, 0x0_E000_0000,
            0x1_0000_0000, 0x1_2000_0000, 0x1_4000_0000, 0x1_6000_0000, 
            0x1_8000_0000, 0x1_A000_0000, 0x1_C000_0000, 0x1_E000_0000
        ]

    def word_size(self) -> int:
        return 64

    def wave_data_addr(self, awg_id: int) -> int:
        return self.__wave_src_addrs[awg_id]

    def max_size_for_wave_seq(self) -> int:
        return 512 * 1024 * 1024

    def udp_port(self) -> int:
        return 0x4000


class CaptureUnitParams(object, metaclass = ABCMeta):
    """各種デザインのキャプチャユニットに関連するパラメータを取得するためのインタフェースを規定するクラス."""

    @classmethod
    def of(self, design_type: E7AwgHwType) -> Self:
        if design_type == E7AwgHwType.SIMPLE_MULTI:
            return cast(Self, CaptureUnitParamsSimpleMulti())
               
        raise ValueError('Invalid e7awg_hw type.  ({})'.format(design_type))

    @abstractmethod
    def input_sample_size(self) -> int:
        """キャプチャユニットに入力されるサンプルデータのサイズ (Bytes)"""
        pass

    @abstractmethod
    def input_word_size(self) -> int:
        """
        1 キャプチャワード当たりのサイズ (Bytes)
        
        | キャプチャワード : キャプチャユニットに 1 サイクルで入力されるサンプル群

        """
        pass

    @abstractmethod
    def num_samples_in_input_word(self) -> int:
        """キャプチャユニットに 1 サイクルで入力されるサンプル数"""
        pass

    @abstractmethod
    def output_sample_size(self) -> int:
        """キャプチャユニットが出力するサンプルデータのサイズ (Bytes)"""
        pass

    @abstractmethod
    def classification_result_size(self) -> int:
        """キャプチャユニットが出力する四値化データのサイズ (Bits)"""
        pass

    @abstractmethod
    def max_integ_vec_elems(self) -> int:
        """キャプチャユニットが持つ積算ユニットが保持できる積算値の最大数 """
        pass

    @abstractmethod
    def sampling_rate(self) -> int:
        """キャプチャユニットのサンプリングレート"""
        pass

    @abstractmethod
    def udp_port(self) -> int:
        """キャプチャユニット制御レジスタにアクセスする際に使用する UDP ポート番号"""
        pass


class CaptureUnitParamsSimpleMulti(CaptureUnitParams):
    """Simple Multi デザインのキャプチャユニットのパラメータを保持するクラス"""

    def input_sample_size(self) -> int:
        # I = 16 bits, Q = 16 bits
        return 4

    def input_word_size(self) -> int:
        return self.input_sample_size() * self.num_samples_in_input_word()
    
    def num_samples_in_input_word(self) -> int:
        return 4

    def output_sample_size(self) -> int:
        # I = 32 bits 浮動小数点数, Q = 32 bits 浮動小数点数
        return 8

    def classification_result_size(self) -> int:
        return 2

    def max_integ_vec_elems(self) -> int:
        return 4096

    def sampling_rate(self) -> int:
        return 500_000_000

    def udp_port(self) -> int:
        return 0x4001


class CaptureRamParams(object, metaclass = ABCMeta):
    """各種デザインのキャプチャデータ RAM のパラメータを取得するためのインタフェースを規定するクラス."""

    @classmethod
    def of(self, design_type: E7AwgHwType) -> Self:
        if design_type == E7AwgHwType.SIMPLE_MULTI:
            return cast(Self, CaptureRamParamsSimpleMulti())
               
        raise ValueError('Invalid e7awg_hw type.  ({})'.format(design_type))

    @abstractmethod
    def word_size(self) -> int:
        """キャプチャデータ RAM のワードサイズ (Bytes)"""
        pass

    @abstractmethod
    def capture_data_addr(self, capture_unit_id: int) -> int:
        """
        引数で指定したキャプチャユニットのキャプチャデータを格納するキャプチャデータ RAM のアドレスを返す
        
        | capture_data_addr(n) = キャプチャユニット n のキャプチャデータ格納先アドレス

        """
        pass

    @abstractmethod
    def max_size_for_capture_data(self) -> int:
        """ 1 キャプチャデータに割り当てられる最大 RAM サイズ (Bytes)"""
        pass

    @abstractmethod
    def udp_port(self) -> int:
        """キャプチャデータ RAM にアクセスする際に使用する UDP ポート番号"""
        pass


class CaptureRamParamsSimpleMulti(CaptureRamParams):
    """Simple Multi デザインのキャプチャデータ RAM のパラメータを保持するクラス"""

    def __init__(self) -> None:
        self.__capture_addrs: Final = [
            0x0_1000_0000, 0x0_3000_0000, 0x0_5000_0000, 0x0_7000_0000,
            0x0_9000_0000, 0x0_B000_0000, 0x0_D000_0000, 0x0_F000_0000,
            0x1_5000_0000, 0x1_7000_0000
        ]

    def word_size(self) -> int:
        return 32

    def capture_data_addr(self, awg_id: int) -> int:
        return self.__capture_addrs[awg_id]

    def max_size_for_capture_data(self) -> int:
        return 256 * 1024 * 1024

    def udp_port(self) -> int:
        return 0x4000
