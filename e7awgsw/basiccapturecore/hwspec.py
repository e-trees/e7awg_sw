from typing import cast
from typing_extensions import Self
from collections.abc import Collection
from .captureparam import CaptureParam
from .hwparam import CaptureUnitParams
from .hwdefs import DspUnit
from ..hwparam import CaptureRamParams
from ..hwdefs import E7AwgHwType, SampleDataType

class CaptureUnitSpecs:
    """キャプチャユニットの性能値をまとめたクラス"""

    @classmethod
    def _create(self, design_type: E7AwgHwType) -> Self:
        if design_type == E7AwgHwType.ZCU111_DAC_6G_URAM_X2:
            specs = CaptureUnitSpecs(
                CaptureUnitParams.of(design_type),
                CaptureRamParams.of(design_type))
            return cast(Self, specs)
               
        raise ValueError('Invalid e7awg_hw type.  ({})'.format(design_type))


    def __init__(
        self,
        cap_unit_params: CaptureUnitParams,
        cap_ram_params: CaptureRamParams) -> None:
        self.__cap_unit_params = cap_unit_params
        self.__cap_ram_params = cap_ram_params


    def max_capture_samples(
        self,
        data_type: SampleDataType,
        dsp_units: Collection[DspUnit] = []) -> int:
        """引数に指定した条件でキャプチャユニットが保存可能なサンプル数を返す.

        | ここでは, サンプルとはキャプチャユニットに入力された生データだけでなく, 
        | 総和や二値化などの信号処理で算出される個々のデータのことも指す.
        |
        | I/Q データを処理してそれぞれの相から結果が得られる場合, 2 つの結果をまとめて 1 サンプルとカウントする.

        Args:
            data_type: キャプチャユニットに入力されるデータの型
            dsp_units: 適用される信号処理の種類を格納したコレクション

        Returns:
            int: キャプチャユニットが保存可能なサンプル数
        """
        mem_size = self.__cap_ram_params.max_size_for_capture_data() * 8
        return mem_size // self.__cap_unit_params.capture_sample_size(data_type, *dsp_units)


    def num_capture_samples(self, param: CaptureParam) -> int:
        """引数に指定したキャプチャパラメータでキャプチャユニットが出力するサンプル数を返す.

        | ここでは, サンプルとはキャプチャユニットに入力された生データだけでなく, 
        | 総和や二値化などの信号処理で算出される個々のデータのことも指す.
        |
        | I/Q データを処理してそれぞれの相から結果が得られる場合, 2 つの結果をまとめて 1 サンプルとカウントする.

        Args:
            param: このキャプチャパラメータでキャプチャしたときのサンプル数を返す

        Returns:
            int: キャプチャユニットが出力するサンプル数
        """
        dsp_list = param.dsp_list
        # 各キャプチャステップのキャプチャターゲットのサンプル数を格納したリスト
        num_cap_samples_list = [
            num_cap_samples * self.num_samples_in_capture_word
            for num_cap_samples, _ in param.capture_steps]

        if DspUnit.SUM in dsp_list:
            num_sum_samples = param.num_sum_words * self.num_samples_in_capture_word
            num_cap_samples_list = [
                num_cap_samples // num_sum_samples for num_cap_samples in num_cap_samples_list]

        if DspUnit.REDUCTION in dsp_list:
            num_cap_samples_list = [
                0 if num_cap_samples == 0 else 1 for num_cap_samples in num_cap_samples_list]
        
        return sum(num_cap_samples_list)


    @property
    def num_samples_in_capture_word(self) -> int:
        """キャプチャワード (= キャプチャユニットに入力されるサンプルを複数まとめたもの) に含まれるサンプル数
        
        | I/Q データはまとめて 1 サンプルと数える

        """
        return self.__cap_unit_params.num_samples_in_capture_word()


    @property
    def min_capture_steps(self) -> int:
        """キャプチャ区間を構成可能な最小のキャプチャステップの数"""
        return self.__cap_unit_params.min_capture_steps()


    @property
    def max_capture_steps(self) -> int:
        """キャプチャ区間を構成可能な最大のキャプチャステップの数"""
        return self.__cap_unit_params.max_capture_steps()


    @property
    def min_capture_target_len(self) -> int:
        """キャプチャターゲット長として指定可能な最小の値 (単位: キャプチャワード)"""
        return self.__cap_unit_params.min_capture_target_len()


    @property
    def max_capture_target_len(self) -> int:
        """キャプチャターゲット長として指定可能な最大の値 (単位: キャプチャワード)"""
        return self.__cap_unit_params.max_capture_target_len()


    @property
    def min_post_blank_len(self) -> int:
        """ポストブランク長として指定可能な最小の値 (単位: キャプチャワード)"""
        return self.__cap_unit_params.min_post_blank_len()

    @property
    def max_post_blank_len(self) -> int:
        """ポストブランク長として指定可能な最小の値 (単位: キャプチャワード)"""
        return self.__cap_unit_params.max_post_blank_len()


    @property
    def min_capture_delay(self) -> int:
        """キャプチャディレイとして指定可能な最小の値 (単位: キャプチャワード)"""
        return self.__cap_unit_params.min_capture_delay()


    @property
    def max_capture_delay(self) -> int:
        """キャプチャディレイとして指定可能な最大の値 (単位: キャプチャワード)"""
        return self.__cap_unit_params.max_capture_delay()

    
    @property
    def min_sum_words(self) -> int:
        """総和ワード数として指定可能な最小の値  (単位: キャプチャワード)"""
        return self.__cap_unit_params.min_sum_words()


    @property
    def max_sum_words(self) -> int:
        """総和ワード数として指定可能な最大の値  (単位: キャプチャワード)"""
        return self.__cap_unit_params.max_sum_words()


    @property
    def min_bin_threshold(self) -> int:
        """二値化閾値として指定可能な最小の値  (単位: キャプチャワード)"""
        return self.__cap_unit_params.min_bin_threshold()


    @property
    def max_bin_threshold(self) -> int:
        """二値化閾値として指定可能な最大の値  (単位: キャプチャワード)"""
        return self.__cap_unit_params.max_bin_threshold()


    @property
    def sampling_rate(self) -> int:
        """キャプチャユニットのサンプリングレート.

        Returns:
            キャプチャユニットのサンプリングレート (単位: サンプル数/秒)
        """
        return self.__cap_unit_params.sampling_rate()
