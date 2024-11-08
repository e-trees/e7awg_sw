from typing import Optional
from .hwdefs import E7AwgHwType
from .hwparam import AwgParams, CaptureUnitParams, CaptureRamParams

class AwgSpecs:
    
    def __init__(self, awg_params: AwgParams) -> None:
        """AWG の性能値をまとめたクラス"""
        self.__awg_params = awg_params


    @property
    def sampling_rate(self) -> int:
        """AWG のサンプリングレート.

        Returns:
            AWG のサンプリングレート (単位: サンプル数/秒)
        """
        return self.__awg_params.sampling_rate()


    @property
    def max_post_blank(self) -> int:
        """波形チャンクに指定可能な最大ポストブランク長 (単位: AWG ワード)

        Returns:
            int: 波形チャンクに指定可能な最大ポストブランク長
        """
        return 0xFFFF_FFFF


    @property
    def max_chunk_repeats(self) -> int:
        """波形チャンクの最大リピート回数
        
        Returns:
            int: 波形チャンクの最大リピート回数
        """
        return 0xFFFF_FFFF


    @property
    def max_wait_words(self) -> int:
        """波形シーケンスの先頭に付く 0 データの最大の長さ (単位: AWG ワード)
        
        Returns:
            int: 波形シーケンスの先頭に付く 0 データの最大の長さ
        """
        return 0xFFFF_FFFF


    @property
    def max_sequence_repeats(self) -> int:
        """波形シーケンスの最大リピート回数
        
        Returns:
            int: 波形シーケンスの最大リピート回数
        """
        return 0xFFFF_FFFF


    @property
    def max_chunks(self) -> int:
        """波形シーケンスに登録可能な最大チャンク数
        
        Returns:
            int: 波形シーケンスに登録可能な最大チャンク数
        """
        return 16


    @property
    def num_samples_in_wave_block(self) -> int:
        """ 1 波形ブロックに含まれるサンプル数
        
        Returns:
            int: 1 波形ブロックに含まれるサンプル数
        """
        return self.__awg_params.num_sample_in_wave_block()


    @property
    def smallest_unit_of_wave_len(self) -> int:
        """波形チャンクの波形パート (= ポストブランクではない部分) を構成可能なサンプル数の最小単位
        
        Returns:
            int: 波形チャンクの波形パートを構成可能なサンプル数の最小単位
        """
        return self.__awg_params.smallest_unit_of_wave_len()


    @property
    def num_samples_in_word(self) -> int:
        """ 1 AWG ワード当たりのサンプル数
        
        | e7awg_hw の種類によって異なる. (I/Q データの場合は 2 相まとめて 1 サンプルとカウント)
        |     simple multi : 4 サンプル
        |     KR260        : 1 サンプル
        |     ZCU111       : 8 サンプル

        Returns:
            int: 1 AWG ワード当たりのサンプル数
        """
        return self.__awg_params.num_samples_in_word()


    @property
    def sample_size(self):
        """
        AWG が出力する 1 サンプルのサイズ.  (Bytes)
        
        | I/Q データの場合は 2 相まとめて 1 サンプルとカウント

        Return:
            int: AWG が出力する 1 サンプルのサイズ.
        """
        return self.__awg_params.sample_size()


class CaptureUnitSpecs:

    def __init__(self, cap_unit_params: CaptureUnitParams, cap_ram_params: CaptureRamParams) -> None:
        """キャプチャユニットの性能値をまとめたクラス"""
        self.__cap_unit_params = cap_unit_params
        self.__cap_ram_params = cap_ram_params


    @property
    def max_capture_samples(self) -> int:
        """ 1 キャプチャユニットが保存可能なサンプル数.

        Returns:
            1 キャプチャユニットが保存可能なサンプル数
        """
        return self.__cap_ram_params.max_size_for_capture_data() \
            // self.__cap_unit_params.output_sample_size()


    @property
    def max_classification_results(self) -> int:
        """ 1 キャプチャユニットが保存可能な四値化結果の数.

        Returns:
            1 キャプチャユニットが保存可能な四値化結果の数
        """
        return self.__cap_ram_params.max_size_for_capture_data() * 8 \
            // self.__cap_unit_params.classification_result_size()


    @property
    def sampling_rate(self) -> int:
        """キャプチャユニットのサンプリングレート.

        Returns:
            キャプチャユニットのサンプリングレート (単位: サンプル数/秒)
        """
        return self.__cap_unit_params.sampling_rate()


class E7AwgHwSpecs:

    def __init__(self, design_type: E7AwgHwType) -> None:
        """
        e7awg_hw の性能値 (AWG のサンプリングレートなど) を取得するクラス

        Args:
            design_type (E7AwgHwType): 性能値を取得する e7awg_hw の種類
        """
        self.__design_type = design_type
        self.__awg_params = AwgParams.of(design_type)
        self.__awg_specs = AwgSpecs(self.__awg_params)

        self.__cap_unit_params: Optional[CaptureUnitParams] = None
        self.__cap_ram_params: Optional[CaptureRamParams] = None
        self.__cap_unit_specs: Optional[CaptureUnitSpecs] = None
        if design_type == E7AwgHwType.SIMPLE_MULTI:
            self.__cap_unit_params = CaptureUnitParams.of(design_type)
            self.__cap_ram_params = CaptureRamParams.of(design_type)
            self.__cap_unit_specs = CaptureUnitSpecs(self.__cap_unit_params, self.__cap_ram_params)


    @property
    def design_type(self) -> E7AwgHwType:
        return self.__design_type


    @property
    def awg(self) -> Optional[AwgSpecs]:
        """AWG の性能値をまとめたオブジェクト"""
        return self.__awg_specs


    @property
    def cap_unit(self) -> Optional[CaptureUnitSpecs]:
        """キャプチャユニットの性能値をまとめたオブジェクト"""
        return self.__cap_unit_specs
