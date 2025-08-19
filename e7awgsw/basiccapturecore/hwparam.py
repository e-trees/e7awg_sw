from typing import cast
from abc import ABCMeta, abstractmethod
from typing_extensions import Self
from ..hwdefs import E7AwgHwType, SampleDataType
from .hwdefs import DspUnit

class CaptureUnitParams(object, metaclass = ABCMeta):
    """各種デザインのキャプチャユニットに関連するパラメータを取得するためのインタフェースを規定するクラス."""

    @classmethod
    def of(self, design_type: E7AwgHwType) -> Self:
        if design_type == E7AwgHwType.ZCU111_DAC_6G_URAM_X2:
            return cast(Self, CaptureUnitParamsZcu111Dac6gUramX2())
               
        raise ValueError('Invalid e7awg_hw type.  ({})'.format(design_type))

    @abstractmethod
    def num_samples_in_capture_word(self) -> int:
        """ 1 キャプチャワードに含まれるサンプル数

        | I/Q データはまとめて 1 サンプルと数える

        """
        pass

    @abstractmethod
    def min_capture_steps(self) -> int:
        """キャプチャ区間を構成可能な最小のキャプチャステップの数"""
        pass

    @abstractmethod
    def max_capture_steps(self) -> int:
        """キャプチャ区間を構成可能な最大のキャプチャステップの数"""
        pass

    @abstractmethod
    def min_capture_target_len(self) -> int:
        """キャプチャターゲット長として指定可能な最小の値 (単位: キャプチャワード)"""
        pass

    @abstractmethod
    def max_capture_target_len(self) -> int:
        """キャプチャターゲット長として指定可能な最大の値 (単位: キャプチャワード)"""
        pass

    @abstractmethod
    def min_post_blank_len(self) -> int:
        """ポストブランク長として指定可能な最小の値 (単位: キャプチャワード)"""
        pass

    @abstractmethod
    def max_post_blank_len(self) -> int:
        """ポストブランク長として指定可能な最小の値 (単位: キャプチャワード)"""
        pass

    @abstractmethod
    def min_capture_delay(self) -> int:
        """キャプチャディレイとして指定可能な最小の値 (単位: キャプチャワード)"""
        pass

    @abstractmethod
    def max_capture_delay(self) -> int:
        """キャプチャディレイとして指定可能な最大の値 (単位: キャプチャワード)"""
        pass

    @abstractmethod
    def min_sum_words(self) -> int:
        """総和ワード数として指定可能な最小の値  (単位: キャプチャワード)"""
        pass

    @abstractmethod
    def max_sum_words(self) -> int:
        """総和ワード数として指定可能な最大の値  (単位: キャプチャワード)"""
        pass

    @abstractmethod
    def min_bin_threshold(self) -> int:
        """二値化閾値として指定可能な最小の値  (単位: キャプチャワード)"""
        pass

    @abstractmethod
    def max_bin_threshold(self) -> int:
        """二値化閾値として指定可能な最大の値  (単位: キャプチャワード)"""
        pass

    @abstractmethod
    def capture_sample_size(self, data_type: SampleDataType, *dsp_list: DspUnit):
        """キャプチャされたサンプルのサイズ (単位: Bits)"""
        pass

    @abstractmethod
    def is_capture_sample_signed(self, *dsp_list: DspUnit):
        """キャプチャされたサンプルが符号付整数の場合 true"""
        pass

    @abstractmethod
    def sampling_rate(self) -> int:
        """キャプチャユニットのサンプリングレート"""
        pass

    @abstractmethod
    def udp_port(self) -> int:
        """キャプチャユニット制御レジスタにアクセスする際に使用する UDP ポート番号"""
        pass


class CaptureUnitParamsZcu111Dac6gUramX2(CaptureUnitParams):
    """以下の構成の ZCU111 デザインのキャプチャユニットのパラメータを保持するクラス
    
    | DAC : 6.51264 Gsps
    | 波形データ RAM : DRAM x1, URAM x2

    """

    def num_samples_in_capture_word(self) -> int:
        return 8

    def min_capture_steps(self) -> int:
        return 1
    
    def max_capture_steps(self) -> int:
        return 1024

    def min_capture_target_len(self) -> int:
        return 1

    def max_capture_target_len(self) -> int:
        return 0xFFFF_FFFF

    def min_post_blank_len(self) -> int:
        return 1

    def max_post_blank_len(self) -> int:
        return 0xFFFF_FFFF

    def min_capture_delay(self) -> int:
        return 0

    def max_capture_delay(self) -> int:
        return 0xFFFF_FFFF

    def min_sum_words(self) -> int:
        return 1

    def max_sum_words(self) -> int:
        return 8192

    def min_bin_threshold(self) -> int:
        return -0x8000_0000

    def max_bin_threshold(self) -> int:
        return 0x7FFF_FFFF

    def __raw_sample_size(self, data_type: SampleDataType) -> int:
        """DSP を適用しない場合の出力サンプルサイズ (単位: Bits)"""
        if data_type == SampleDataType.IQ:
            return 32
        elif data_type == SampleDataType.REAL:
            return 16
        raise AssertionError('unknown data type')

    def __sum_sample_size(self, data_type: SampleDataType) -> int:
        """総和処理の結果のサンプルサイズ (単位: Bits)"""
        if data_type == SampleDataType.IQ:
            return 64
        elif data_type == SampleDataType.REAL:
            return 32
        raise AssertionError('unknown data type')

    def __bin_sample_size(self, data_type: SampleDataType) -> int:
        """二値化処理の結果のサンプルサイズ (単位: Bits)"""
        if data_type == SampleDataType.IQ:
            return 2
        elif data_type == SampleDataType.REAL:
            return 1
        raise AssertionError('unknown data type')

    def __reduction_result_size(self, data_type: SampleDataType) -> int:
        """リダクション処理の結果のサイズ (単位: Bits)"""
        if data_type == SampleDataType.IQ:
            return 2
        elif data_type == SampleDataType.REAL:
            return 1
        raise AssertionError('unknown data type')

    def capture_sample_size(self, data_type: SampleDataType, *dsp_list: DspUnit):
        if DspUnit.REDUCTION in dsp_list:
            return self.__reduction_result_size(data_type)

        if DspUnit.BINARIZATION in dsp_list:
            return self.__bin_sample_size(data_type)
        
        if DspUnit.SUM in dsp_list:
            return self.__sum_sample_size(data_type)
        
        return self.__raw_sample_size(data_type)

    def is_capture_sample_signed(self, *dsp_list: DspUnit):
        if DspUnit.REDUCTION in dsp_list:
            return False

        if DspUnit.BINARIZATION in dsp_list:
            return False
        
        return True

    def sampling_rate(self) -> int:
        return 3_256_320_000

    def udp_port(self) -> int:
        return 0x4001
