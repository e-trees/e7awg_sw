from __future__ import annotations

import socket
import os
import stat
from typing_extensions import Self
from types import TracebackType
from logging import Logger
from abc import ABCMeta, abstractmethod
from .rfdcdefs import DacTile, AdcTile, RfdcInterrupt, DacChannel, AdcChannel
from ..logger import get_file_logger, get_null_logger, log_error
from ..lock import ReentrantFileLock
from ..hwdefs import E7AwgHwType
from ..rfdccommon.rfterr import RfdcCommandError
from ..rfdccommon.rfdcparam import RfdcParams
from ..rfdccommon.validator import RfdcValidator
from ..rfdccommon.rftcmd import RftoolCommand
from ..rfdccommon.rfdcdefs import RfConverter, RfdcIntrpMask, MixerScale
from ..rfdccommon.rftooltransceiver import RftoolTransceiver

class RfdcCtrlBase(object, metaclass = ABCMeta):

    def __init__(
        self,
        transceiver: RftoolTransceiver,
        design_type: E7AwgHwType,
        validate_args: bool,
        enable_lib_log: bool,
        logger: Logger
    ) -> None:
        self._validate_args = validate_args
        self._loggers = [logger]
        if enable_lib_log:
            self._loggers.append(get_file_logger())

        try:
            self._rfdc_params = RfdcParams.of(design_type)
            if self._validate_args:
                self._validator = RfdcValidator(
                    set(DacTile),
                    set(DacChannel),
                    set(AdcTile),
                    set(AdcChannel),
                    self._rfdc_params,
                    set(RfdcInterrupt))
                self._validator.validate_transceiver(transceiver)
                self._validate_design_type(design_type)
        except Exception as e:
            log_error(e, *self._loggers)
            raise


    def set_dac_mixer_settings(
        self,
        tile: DacTile,
        channel: DacChannel,
        freq: float,
        phase: float,
        scale: MixerScale
    ) -> None:
        """DAC のミキサの設定を変更する.

        Args:
            tile (DacTile): 設定を変更するミキサがある DAC のタイル ID
            channel (DacChannel): 設定を変更するミキサがある DAC のチャネル ID
            freq: ミキサの周波数 (単位: MHz, -10000 <= freq <= 10000).   参考 : PG269 (v2.6) p.75
            phase: ミキサの位相  (単位: degrees, -180 < phase < 180).    参考 : PG269 (v2.6) p.208
            scale: ミキサの振幅
        """
        if self._validate_args:
            try:
                self._validator.validate_dac_tile(tile)
                self._validator.validate_dac_channel(channel)
                self._validator.validate_mixer_freq(freq)
                self._validator.validate_mixer_phase(phase)
                self._validator.validate_mixer_scale(scale)
            except Exception as e:
                log_error(e, *self._loggers)
                raise
        
        self._set_dac_mixer_settings(tile, channel, freq, phase, scale)


    def get_dac_mixer_settings(
        self, tile: DacTile, channel: DacChannel) -> tuple[float, float, MixerScale]:
        """DAC のミキサの設定を取得する.

        Args:
            tile (DacTile): 設定を変更するミキサがある DAC のタイル ID
            channel (DacChannel): 設定を変更するミキサがある DAC のチャネル ID

        Returns:
            tuple[float, float, MixerScale]:
                | [0] -> ミキサの周波数 (単位: MHz)
                | [1] -> ミキサの位相  (単位: degrees)
                | [2] -> ミキサの振幅
        """
        if self._validate_args:
            try:
                self._validator.validate_dac_tile(tile)
                self._validator.validate_dac_channel(channel)
            except Exception as e:
                log_error(e, *self._loggers)
                raise
        
        return self._get_dac_mixer_settings(tile, channel)

    def set_adc_mixer_settings(
        self,
        tile: AdcTile,
        channel: AdcChannel,
        enable: bool,
        freq: float,
        phase: float,
        scale: MixerScale
    ) -> None:
        """ADC のミキサの設定を変更する.

        Args:
            tile (AdcTile): 設定を変更するミキサがある ADC のタイル ID
            channel (AdcChannel): 設定を変更するミキサがある ADC のチャネル ID
            enable: ミキサを有効にする場合 True, 無効にする場合 False
            freq: ミキサの周波数 (単位: MHz, -10000 <= freq <= 10000).   参考 : PG269 (v2.6) p.75
            phase: ミキサの位相  (単位: degrees, -180 < phase < 180).    参考 : PG269 (v2.6) p.208
            scale: ミキサの振幅
            update_timing: ミキサに設定を反映するタイミング
        """
        if self._validate_args:
            try:
                self._validator.validate_adc_tile(tile)
                self._validator.validate_adc_channel(channel)
                self._validator.validate_mixer_freq(freq)
                self._validator.validate_mixer_phase(phase)
                self._validator.validate_mixer_scale(scale)
                if not isinstance(enable, bool):
                    raise ValueError("'enable' must be a boolean value.")
            except Exception as e:
                log_error(e, *self._loggers)
                raise
        
        self._set_adc_mixer_settings(tile, channel, enable, freq, phase, scale)


    def get_adc_mixer_settings(
        self, tile: AdcTile, channel: AdcChannel) -> tuple[bool, float, float, MixerScale]:
        """ADC のミキサの設定を取得する.

        Args:
            tile (AdcTile): 設定を変更するミキサがある ADC のタイル ID
            channel (AdcChannel): 設定を変更するミキサがある ADC のチャネル ID

        Returns:
            tuple[float, float, MixerScale]:
                | [0] -> ミキサが有効な場合 True, 無効な場合 False
                | [1] -> ミキサの周波数 (単位: MHz)
                | [2] -> ミキサの位相  (単位: degrees)
                | [3] -> ミキサの振幅
        """
        if self._validate_args:
            try:
                self._validator.validate_adc_tile(tile)
                self._validator.validate_adc_channel(channel)
            except Exception as e:
                log_error(e, *self._loggers)
                raise
        
        return self._get_adc_mixer_settings(tile, channel)


    def sync_dac_tiles(self):
        """全ての DAC タイルを同期させる.
        このメソッドを呼ぶ前に, DAC の I/Q ミキサの設定を完了させておくこと.
        """
        self._sync_dac_tiles()


    def sync_adc_tiles(self):
        """全ての ADC タイルを同期させる.
        このメソッドを呼ぶ前に, ADC の I/Q ミキサの設定を完了させておくこと.
        """
        self._sync_adc_tiles()


    def sync_dac_adc_tiles(self):
        """全ての DAC と ADC タイルを同期させる.
        このメソッドを呼ぶ前に, DAC および ADC の I/Q ミキサの設定を完了させておくこと.
        """
        self._sync_dac_adc_tiles()


    def get_dac_interrupts(self, tile: DacTile, channel: DacChannel) -> list[RfdcInterrupt]:
        """引数で指定した DAC の割り込みを取得する.

        Args:
            tile (DacTile): 割り込みを調べる DAC のタイル ID
            channel (DacChannel): 割り込みを調べる DAC のチャネル ID

        Returns:
            list[RfdcInterrupt]:
                | 発生した割り込みのリスト.
                | 割り込みが無かった場合は空のリスト.
        """
        if self._validate_args:
            try:
                self._validator.validate_dac_tile(tile)
                self._validator.validate_dac_channel(channel)
            except Exception as e:
                log_error(e, *self._loggers)
                raise
        
        return self._get_dac_interrupts(tile, channel)


    def get_adc_interrupts(self, tile: AdcTile, channel: AdcChannel) -> list[RfdcInterrupt]:
        """引数で指定した ADC の割り込みを取得する.

        Args:
            tile (AdcTile): 割り込みを調べる ADC のタイル ID
            channel (AdcChannel): 割り込みを調べる ADC のチャネル ID

        Returns:
            list[RfdcInterrupt]:
                | 発生した割り込みのリスト.
                | 割り込みが無かった場合は空のリスト.
        """
        if self._validate_args:
            try:
                self._validator.validate_adc_tile(tile)
                self._validator.validate_adc_channel(channel)
            except Exception as e:
                log_error(e, *self._loggers)
                raise
        
        return self._get_adc_interrupts(tile, channel)


    def enable_dac_interrupts(
        self, tile: DacTile, channel: DacChannel, *flags: RfdcInterrupt) -> None:
        """引数で指定した DAC の割り込みを有効化する.

        Args:
            tile (DacTile): 割り込みの設定を変更する DAC のタイル ID
            channel (DacChannel): 割り込みの設定を変更する DAC のチャネル ID
            flags (RfdcInterrupt): 有効化する割り込み
        """
        if self._validate_args:
            try:
                self._validator.validate_dac_tile(tile)
                self._validator.validate_dac_channel(channel)
                self._validator.validate_rfdc_interrupts(*set(flags))
            except Exception as e:
                log_error(e, *self._loggers)
                raise
        
        return self._enable_dac_interrupts(tile, channel, *flags)


    def enable_adc_interrupts(
        self, tile: AdcTile, channel: AdcChannel, *flags: RfdcInterrupt) -> None:
        """引数で指定した ADC の割り込みを有効化する.

        Args:
            tile (AdcTile): 割り込みの設定を変更する ADC のタイル ID
            channel (AdcChannel): 割り込みの設定を変更する ADC のチャネル ID
            flags (RfdcInterrupt): 有効化する割り込み
        """
        if self._validate_args:
            try:
                self._validator.validate_adc_tile(tile)
                self._validator.validate_adc_channel(channel)
                self._validator.validate_rfdc_interrupts(*set(flags))
            except Exception as e:
                log_error(e, *self._loggers)
                raise
        
        return self._enable_adc_interrupts(tile, channel, *flags)


    def disable_dac_interrupts(
        self, tile: DacTile, channel: DacChannel, *flags: RfdcInterrupt) -> None:
        """引数で指定した DAC の割り込みを無効化する.

        Args:
            tile (DacTile): 割り込みの設定を変更する DAC のタイル ID
            channel (DacChannel): 割り込みの設定を変更する DAC のチャネル ID
            flags (RfdcInterrupt): 無効化する割り込み
        """
        if self._validate_args:
            try:
                self._validator.validate_dac_tile(tile)
                self._validator.validate_dac_channel(channel)
                self._validator.validate_rfdc_interrupts(*set(flags))
            except Exception as e:
                log_error(e, *self._loggers)
                raise
        
        return self._disable_dac_interrupts(tile, channel, *flags)


    def disable_adc_interrupts(
        self, tile: AdcTile, channel: AdcChannel, *flags: RfdcInterrupt) -> None:
        """引数で指定した ADC の割り込みを無効化する.

        Args:
            tile (AdcTile): 割り込みの設定を変更する ADC のタイル ID
            channel (AdcChannel): 割り込みの設定を変更する ADC のチャネル ID
            flags (RfdcInterrupt): 無効化する割り込み
        """
        if self._validate_args:
            try:
                self._validator.validate_adc_tile(tile)
                self._validator.validate_adc_channel(channel)
                self._validator.validate_rfdc_interrupts(*set(flags))
            except Exception as e:
                log_error(e, *self._loggers)
                raise
        
        return self._disable_adc_interrupts(tile, channel, *flags)


    def clear_dac_interrupts(
        self, tile: DacTile, channel: DacChannel, *flags: RfdcInterrupt) -> None:
        """引数で指定した DAC の割り込みフラグをクリアする.

        Args:
            tile (DacTile): 割り込みフラグをクリアする DAC のタイル ID
            channel (DacChannel): 割り込みフラグをクリアする DAC のチャネル ID
            flags (RfdcInterrupt): フラグをクリアする割り込み
        """
        if self._validate_args:
            try:
                self._validator.validate_dac_tile(tile)
                self._validator.validate_dac_channel(channel)
                self._validator.validate_rfdc_interrupts(*set(flags))
            except Exception as e:
                log_error(e, *self._loggers)
                raise
        
        return self._clear_dac_interrupts(tile, channel, *flags)


    def clear_adc_interrupts(
        self, tile: AdcTile, channel: AdcChannel, *flags: RfdcInterrupt) -> None:
        """引数で指定した ADC の割り込みフラグをクリアする.

        Args:
            tile (AdccTile): 割り込みフラグをクリアする ADC のタイル ID
            channel (AdcChannel): 割り込みフラグをクリアする ADC のチャネル ID
            flags (RfdcInterrupt): フラグをクリアする割り込み
        """
        if self._validate_args:
            try:
                self._validator.validate_adc_tile(tile)
                self._validator.validate_adc_channel(channel)
                self._validator.validate_rfdc_interrupts(*set(flags))
            except Exception as e:
                log_error(e, *self._loggers)
                raise
        
        return self._clear_adc_interrupts(tile, channel, *flags)


    def get_dac_sampling_rate(self, tile: DacTile) -> float:
        """引数で指定した DAC のサンプリングレートを取得する.

        | 同じタイルの DAC のサンプリングレートは共通.

        Args:
            tile (DacTile): サンプリングレートを取得する DAC のタイル ID

        Returns:
            float: サンプリングレート (単位: Msps).  DAC が無効になっている場合は 0 を返す.
        """
        if self._validate_args:
            try:
                self._validator.validate_dac_tile(tile)
            except Exception as e:
                log_error(e, *self._loggers)
                raise
        
        return self._get_dac_sampling_rate(tile)


    def get_adc_sampling_rate(self, tile: AdcTile) -> float:
        """引数で指定した ADC のサンプリングレートを取得する.

        | 同じタイルの ADC のサンプリングレートは共通.

        Args:
            tile (AdcTile): サンプリングレートを取得する ADC のタイル ID

        Returns:
            float: サンプリングレート (単位: Msps).  ADC が無効になっている場合は 0 を返す.
        """
        if self._validate_args:
            try:
                self._validator.validate_adc_tile(tile)
            except Exception as e:
                log_error(e, *self._loggers)
                raise
        
        return self._get_adc_sampling_rate(tile)


    def enable_dac_fifo(self, tile: DacTile) -> None:
        """引数で指定した DAC に波形データを渡すための FIFO を有効化する.

        Args:
            tile (DacTile): FIFO を有効にする DAC のタイル ID
        """
        if self._validate_args:
            try:
                self._validator.validate_dac_tile(tile)
            except Exception as e:
                log_error(e, *self._loggers)
                raise
        
        return self._enable_dac_fifo(tile)


    def enable_adc_fifo(self, tile: AdcTile) -> None:
        """引数で指定した ADC に波形データを渡すための FIFO を有効化する.

        Args:
            tile (AdcTile): FIFO を有効にする ADC のタイル ID
        """
        if self._validate_args:
            try:
                self._validator.validate_adc_tile(tile)
            except Exception as e:
                log_error(e, *self._loggers)
                raise
        
        return self._enable_adc_fifo(tile)


    def disable_dac_fifo(self, tile: DacTile) -> None:
        """引数で指定した DAC に波形データを渡すための FIFO を無効化する.

        Args:
            tile (DacTile): FIFO を無効にする DAC のタイル ID
        """
        if self._validate_args:
            try:
                self._validator.validate_dac_tile(tile)
            except Exception as e:
                log_error(e, *self._loggers)
                raise
        
        return self._disable_dac_fifo(tile)
    

    def disable_adc_fifo(self, tile: AdcTile) -> None:
        """引数で指定した ADC に波形データを渡すための FIFO を無効化する.

        Args:
            tile (AdcTile): FIFO を無効にする ADC のタイル ID
        """
        if self._validate_args:
            try:
                self._validator.validate_adc_tile(tile)
            except Exception as e:
                log_error(e, *self._loggers)
                raise
        
        return self._disable_adc_fifo(tile)


    def enable_adc_calibration_adjustment(self, tile: AdcTile, channel: AdcChannel) -> None:
        """引数で指定した ADC のキャリブレーションパラメータの更新を有効化する.

        Args:
            tile (AdcTile): キャリブレーションパラメータの更新を有効化する ADC のタイル ID
            channel (AdcChannerl): キャリブレーションパラメータの更新を有効化する ADC のチャネル ID
        """
        if self._validate_args:
            try:
                self._validator.validate_adc_tile(tile)
                self._validator.validate_adc_channel(channel)
            except Exception as e:
                log_error(e, *self._loggers)
                raise
        
        return self._enable_adc_calibration_adjustment(tile, channel)


    def disable_adc_calibration_adjustment(self, tile: AdcTile, channel: AdcChannel) -> None:
        """引数で指定した ADC のキャリブレーションパラメータの更新を無効化する.

        | このメソッドを呼んだ後の ADC キャリブレーションは, 更新を無効化する前のキャリブレーションパラメータを用いて行われる

        Args:
            tile (AdcTile): キャリブレーションパラメータの更新を無効化する ADC のタイル ID
            channel (AdcChannerl): キャリブレーションパラメータの更新を無効化する ADC のチャネル ID
        """
        if self._validate_args:
            try:
                self._validator.validate_adc_tile(tile)
                self._validator.validate_adc_channel(channel)
            except Exception as e:
                log_error(e, *self._loggers)
                raise
        
        return self._disable_adc_calibration_adjustment(tile, channel)


    def is_adc_calibration_adjustment_enabled(self, tile: AdcTile, channel: AdcChannel) -> bool:
        if self._validate_args:
            try:
                self._validator.validate_adc_tile(tile)
                self._validator.validate_adc_channel(channel)
            except Exception as e:
                log_error(e, *self._loggers)
                raise
        
        return self._is_adc_calibration_adjustment_enabled(tile, channel)


    def _validate_design_type(self, design_type: E7AwgHwType) -> None:
        if design_type != E7AwgHwType.ZCU111_URAM_X2 and \
           design_type != E7AwgHwType.ZCU111_DAC_6G_URAM_X2 and \
           design_type != E7AwgHwType.ZCU111_DOUBLE_QUANTUM_DOT:
            raise ValueError("Cannot control the RF Data Converter in {}.".format(design_type))

    @abstractmethod
    def _set_dac_mixer_settings(
        self,
        tile: DacTile,
        channel: DacChannel,
        freq: float,
        phase: float,
        scale: MixerScale) -> None:
        pass

    @abstractmethod
    def _get_dac_mixer_settings(
        self, tile: DacTile, channel: DacChannel) -> tuple[float, float, MixerScale]:
        pass

    @abstractmethod
    def _set_adc_mixer_settings(
        self,
        tile: AdcTile,
        channel: AdcChannel,
        enable: bool,
        freq: float,
        phase: float,
        scale: MixerScale) -> None:
        pass

    @abstractmethod
    def _get_adc_mixer_settings(
        self, tile: AdcTile, channel: AdcChannel) -> tuple[bool, float, float, MixerScale]:
        pass

    @abstractmethod
    def _sync_dac_tiles(self) -> None:
        pass

    @abstractmethod
    def _sync_adc_tiles(self) -> None:
        pass

    @abstractmethod
    def _sync_dac_adc_tiles(self) -> None:
        pass

    @abstractmethod
    def _get_dac_interrupts(self, tile: DacTile, channel: DacChannel) -> list[RfdcInterrupt]:
        pass

    @abstractmethod
    def _get_adc_interrupts(self, tile: AdcTile, channel: AdcChannel) -> list[RfdcInterrupt]:
        pass

    @abstractmethod
    def _enable_dac_interrupts(
        self, tile: DacTile, channel: DacChannel, *flags: RfdcInterrupt) -> None:
        pass

    @abstractmethod
    def _enable_adc_interrupts(
        self, tile: AdcTile, channel: AdcChannel, *flags: RfdcInterrupt) -> None:
        pass

    @abstractmethod
    def _disable_dac_interrupts(
        self, tile: DacTile, channel: DacChannel, *flags: RfdcInterrupt) -> None:
        pass

    @abstractmethod
    def _disable_adc_interrupts(
        self, tile: AdcTile, channel: AdcChannel, *flags: RfdcInterrupt) -> None:
        pass

    @abstractmethod
    def _clear_dac_interrupts(
        self, tile: DacTile, channel: DacChannel, *flags: RfdcInterrupt) -> None:
        pass

    @abstractmethod
    def _clear_adc_interrupts(
        self, tile: AdcTile, channel: AdcChannel, *flags: RfdcInterrupt) -> None:
        pass

    @abstractmethod
    def _get_dac_sampling_rate(self, tile: DacTile) -> float:
        pass

    @abstractmethod
    def _get_adc_sampling_rate(self, tile: AdcTile) -> float:
        pass

    @abstractmethod
    def _enable_dac_fifo(self, tile: DacTile) -> None:
        pass

    @abstractmethod
    def _enable_adc_fifo(self, tile: AdcTile) -> None:
        pass

    @abstractmethod
    def _disable_dac_fifo(self, tile: DacTile) -> None:
        pass

    @abstractmethod
    def _disable_adc_fifo(self, tile: AdcTile) -> None:
        pass

    @abstractmethod
    def _enable_adc_calibration_adjustment(self, tile: AdcTile, channel: AdcChannel):
        pass

    @abstractmethod
    def _disable_adc_calibration_adjustment(self, tile: AdcTile, channel: AdcChannel):
        pass

    @abstractmethod
    def _is_adc_calibration_adjustment_enabled(self, tile: AdcTile, channel: AdcChannel):
        pass


class RfdcCtrl(RfdcCtrlBase):

    def __init__(
        self,
        transceiver: RftoolTransceiver,
        design_type: E7AwgHwType,
        *,
        validate_args: bool = True,
        enable_lib_log: bool = True,
        logger: Logger = get_null_logger()
    ) -> None:
        """
        RF Data Converter を持つ e7awg_hw 専用

        Args:
            transceiver (RftoolTransceiver): ZCU111 上で動作するプログラムとの通信機能を提供するオブジェクト
            design_type (E7AwgHwType):
                | このオブジェクトで制御する RF Data Converter が含まれる e7awg_hw の種類
                | RF Data Converter を持つデザインを指定すること.
            validate_args (bool):
                | True -> 引数のチェックを行う
                | False -> 引数のチェックを行わない
            enable_lib_log (bool):
                | True -> ライブラリの標準のログ機能を有効にする.
                | False -> ライブラリの標準のログ機能を無効にする.
            logger (logging.Logger): ユーザ独自のログ出力に用いる Logger オブジェクト
        """
        super().__init__(transceiver, design_type, validate_args, enable_lib_log, logger)
        filepath = '{}/e7awg_{}.lock'.format(
            self.__get_lock_dir(),
            socket.inet_ntoa(socket.inet_aton(transceiver.ip_addr)))
        self.__flock = ReentrantFileLock(filepath)
        self.__command = RftoolCommand(transceiver.ctrl_if)


    def __enter__(self) -> Self:
        return self


    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None
    ) -> None:
        self.close()


    def close(self) -> None:
        """このコントローラと関連付けられたすべてのリソースを開放する.

        | このクラスのインスタンスを with 構文による後処理の対象にした場合, このメソッドを明示的に呼ぶ必要はない.
        | そうでない場合, プログラムを終了する前にこのメソッドを呼ぶこと.

        """
        try:
            self.__flock.discard()
        except Exception as e:
            log_error(e, *self._loggers)
        self.__flock = None  # type: ignore


    def _set_dac_mixer_settings(
        self,
        tile: DacTile,
        channel: DacChannel,
        freq: float,
        phase: float,
        scale: MixerScale) -> None:
        with self.__flock:
            try:
                self.__command.SetMixerSettings(
                    int(RfConverter.DAC),
                    int(tile),
                    int(channel),
                    freq,
                    phase,
                    0,
                    2,
                    0,
                    2,
                    int(scale))
            except Exception as e:
                log_error(e, *self._loggers)
                raise RfdcCommandError(e) from e


    def _get_dac_mixer_settings(
        self, tile: DacTile, channel: DacChannel) -> tuple[float, float, MixerScale]:
        with self.__flock:
            try:
                (type, tile_id, channel_id, freq, phase, 
                event_source, mixer_type, coarse_mixer_freq,
                mixer_mode, scale) = self.__command.GetMixerSettings(
                    int(RfConverter.DAC), int(tile), int(channel))
                return (freq, phase, scale)
            except Exception as e:
                log_error(e, *self._loggers)
                raise RfdcCommandError(e) from e


    def _set_adc_mixer_settings(
        self,
        tile: AdcTile,
        channel: AdcChannel,
        enable: bool,
        freq: float,
        phase: float,
        scale: MixerScale) -> None:
        with self.__flock:
            try:
                mixer_type = 2 if enable else 1
                mixer_mode = 3 if enable else 4
                self.__command.SetMixerSettings(
                    int(RfConverter.ADC),
                    int(tile),
                    int(channel),
                    freq,
                    phase,
                    2,
                    mixer_type,
                    16,
                    mixer_mode,
                    int(scale))
                
                # ADC の I/Q ミキサの設定更新に Immediate イベントが使えないので, Tile イベントを指定して 
                # UpdateEvent で更新する
                self.__command.UpdateEvent(
                    int(RfConverter.ADC),
                    int(tile),
                    int(channel),
                    1)                
            except Exception as e:
                log_error(e, *self._loggers)
                raise RfdcCommandError(e) from e


    def _get_adc_mixer_settings(
        self, tile: AdcTile, channel: AdcChannel) -> tuple[bool, float, float, MixerScale]:
        with self.__flock:
            try:
                (type, tile_id, channel_id, freq, phase, 
                event_source, mixer_type, coarse_mixer_freq,
                mixer_mode, scale) = self.__command.GetMixerSettings(
                    int(RfConverter.ADC), int(tile), int(channel))
                enable = (mixer_mode == 3) and (mixer_type == 2)
                print('tile_id', 'channel_id', 'freq', 'phase', 'event_source', 'mixer_type', 'coarse_mixer_freq', 'mixer_mode', 'scale')
                print(tile_id, channel_id, freq, phase, event_source, mixer_type, coarse_mixer_freq, mixer_mode, scale)
                return (enable, freq, phase, scale)
            except Exception as e:
                log_error(e, *self._loggers)
                raise RfdcCommandError(e) from e


    def _sync_dac_tiles(self) -> None:
        with self.__flock:
            try:
                self.__command.SyncDacTiles()
            except Exception as e:
                log_error(e, *self._loggers)
                raise RfdcCommandError(e) from e


    def _sync_adc_tiles(self) -> None:
        with self.__flock:
            try:
                self.__command.SyncAdcTiles()
            except Exception as e:
                log_error(e, *self._loggers)
                raise RfdcCommandError(e) from e


    def _sync_dac_adc_tiles(self) -> None:
        with self.__flock:
            try:
                self.__command.SyncDacAdcTiles()
            except Exception as e:
                log_error(e, *self._loggers)
                raise RfdcCommandError(e) from e


    def _get_dac_interrupts(self, tile: DacTile, channel: DacChannel) -> list[RfdcInterrupt]:
        with self.__flock:
            flags = self.__command.GetIntrStatus(
                int(RfConverter.DAC), int(tile), int(channel))[3]

        interrupts = []
        if (flags & RfdcIntrpMask.DAC_I_INTP_STG0_OVF or
            flags & RfdcIntrpMask.DAC_I_INTP_STG1_OVF or
            flags & RfdcIntrpMask.DAC_I_INTP_STG2_OVF or
            flags & RfdcIntrpMask.DAC_Q_INTP_STG0_OVF or
            flags & RfdcIntrpMask.DAC_Q_INTP_STG1_OVF or
            flags & RfdcIntrpMask.DAC_Q_INTP_STG2_OVF):
            interrupts.append(RfdcInterrupt.DAC_INTERPOLATION_OVERFLOW)
        if (flags & RfdcIntrpMask.DAC_QMC_GAIN_PHASE_OVF):
            interrupts.append(RfdcInterrupt.DAC_QMC_GAIN_PHASE_OVERFLOW)
        if (flags & RfdcIntrpMask.DAC_QMC_OFFSET_OVF):
            interrupts.append(RfdcInterrupt.DAC_QMC_OFFSET_OVERFLOW)
        if (flags & RfdcIntrpMask.DAC_INV_SINC_OVF):
            interrupts.append(RfdcInterrupt.DAC_INV_SINC_OVERFLOW)
        if (flags & RfdcIntrpMask.DAC_FIFO_OVF):
            interrupts.append(RfdcInterrupt.DAC_FIFO_OVERFLOW)
        if (flags & RfdcIntrpMask.DAC_FIFO_UDF):
            interrupts.append(RfdcInterrupt.DAC_FIFO_UNDERFLOW)
        if (flags & RfdcIntrpMask.DAC_FIFO_MARGIANL_OVF):
            interrupts.append(RfdcInterrupt.DAC_FIFO_MARGINAL_OVERFLOW)
        if (flags & RfdcIntrpMask.DAC_FIFO_MARGIANL_UDF):
            interrupts.append(RfdcInterrupt.DAC_FIFO_MARGINAL_UNDERFLOW)

        return interrupts


    def _get_adc_interrupts(self, tile: AdcTile, channel: AdcChannel) -> list[RfdcInterrupt]:
        with self.__flock:
            flags = self.__command.GetIntrStatus(
                int(RfConverter.ADC), int(tile), int(channel))[3]

        interrupts = []
        if (flags & RfdcIntrpMask.ADC_I_DMON_STG0_OVF or
            flags & RfdcIntrpMask.ADC_I_DMON_STG1_OVF or
            flags & RfdcIntrpMask.ADC_I_DMON_STG2_OVF or
            flags & RfdcIntrpMask.ADC_Q_DMON_STG0_OVF or
            flags & RfdcIntrpMask.ADC_Q_DMON_STG1_OVF or
            flags & RfdcIntrpMask.ADC_Q_DMON_STG2_OVF):
            interrupts.append(RfdcInterrupt.ADC_DECIMATION_OVERFLOW)
        if (flags & RfdcIntrpMask.ADC_QMC_GAIN_PHASE_OVF):
            interrupts.append(RfdcInterrupt.ADC_QMC_GAIN_PHASE_OVERFLOW)
        if (flags & RfdcIntrpMask.ADC_QMC_OFFSET_OVF):
            interrupts.append(RfdcInterrupt.ADC_QMC_OFFSET_OVERFLOW)
        if (flags & RfdcIntrpMask.SUB_ADC0_OVR or
            flags & RfdcIntrpMask.SUB_ADC0_UDR or
            flags & RfdcIntrpMask.SUB_ADC1_OVR or
            flags & RfdcIntrpMask.SUB_ADC1_UDR or
            flags & RfdcIntrpMask.SUB_ADC2_OVR or
            flags & RfdcIntrpMask.SUB_ADC2_UDR or
            flags & RfdcIntrpMask.SUB_ADC3_OVR or
            flags & RfdcIntrpMask.SUB_ADC3_UDR):
            interrupts.append(RfdcInterrupt.SUB_ADC_OVER_RANGE)
        if (flags & RfdcIntrpMask.ADC_OVV):
            interrupts.append(RfdcInterrupt.ADC_OVER_VOLTAGE)
        if (flags & RfdcIntrpMask.ADC_OVR):
            interrupts.append(RfdcInterrupt.ADC_OVER_RANGE)
        if (flags & RfdcIntrpMask.ADC_FIFO_OVF):
            interrupts.append(RfdcInterrupt.ADC_FIFO_OVERFLOW)
        if (flags & RfdcIntrpMask.ADC_FIFO_UDF):
            interrupts.append(RfdcInterrupt.ADC_FIFO_UNDERFLOW)
        if (flags & RfdcIntrpMask.ADC_FIFO_MARGIANL_OVF):
            interrupts.append(RfdcInterrupt.ADC_FIFO_MARGINAL_OVERFLOW)
        if (flags & RfdcIntrpMask.ADC_FIFO_MARGIANL_UDF):
            interrupts.append(RfdcInterrupt.ADC_FIFO_MARGINAL_UNDERFLOW)

        return interrupts


    def _enable_dac_interrupts(
        self, tile: DacTile, channel: DacChannel, *flags: RfdcInterrupt) -> None:
        with self.__flock:
            mask = self.__to_interrupt_mask(*flags)
            self.__command.IntrEnable(int(RfConverter.DAC), int(tile), int(channel), mask)

    def _enable_adc_interrupts(
        self, tile: AdcTile, channel: AdcChannel, *flags: RfdcInterrupt) -> None:
        with self.__flock:
            mask = self.__to_interrupt_mask(*flags)
            self.__command.IntrEnable(int(RfConverter.ADC), int(tile), int(channel), mask)

    def _disable_dac_interrupts(
        self, tile: DacTile, channel: DacChannel, *flags: RfdcInterrupt) -> None:
        with self.__flock:
            mask = self.__to_interrupt_mask(*flags)
            self.__command.IntrDisable(int(RfConverter.DAC), int(tile), int(channel), mask)

    def _disable_adc_interrupts(
        self, tile: AdcTile, channel: AdcChannel, *flags: RfdcInterrupt) -> None:
        with self.__flock:
            mask = self.__to_interrupt_mask(*flags)
            self.__command.IntrDisable(int(RfConverter.ADC), int(tile), int(channel), mask)

    def _clear_dac_interrupts(
        self, tile: DacTile, channel: DacChannel, *flags: RfdcInterrupt) -> None:
        with self.__flock:
            mask = self.__to_interrupt_mask(*flags)
            self.__command.IntrClr(int(RfConverter.DAC), int(tile), int(channel), mask)


    def _clear_adc_interrupts(
        self, tile: AdcTile, channel: AdcChannel, *flags: RfdcInterrupt) -> None:
        with self.__flock:
            mask = self.__to_interrupt_mask(*flags)
            self.__command.IntrClr(int(RfConverter.ADC), int(tile), int(channel), mask)


    def _get_dac_sampling_rate(self, tile: DacTile) -> float:
        with self.__flock:
            config = self.__command.GetDacTileConfig(int(tile))
        enable = config[0]
        sampling_rate = config[2]
        if not bool(enable):
            return 0

        return sampling_rate * 1000 # to MHz


    def _get_adc_sampling_rate(self, tile: AdcTile) -> float:
        with self.__flock:
            config = self.__command.GetAdcTileConfig(int(tile))
        enable = config[0]
        sampling_rate = config[2]
        if not bool(enable):
            return 0

        return sampling_rate * 1000 # to MHz


    def _enable_dac_fifo(self, tile: DacTile) -> None:
        with self.__flock:
            self.__command.SetupFIFO(int(RfConverter.DAC), int(tile), 1)


    def _enable_adc_fifo(self, tile: AdcTile) -> None:
        with self.__flock:
            self.__command.SetupFIFO(int(RfConverter.ADC), int(tile), 1)


    def _disable_dac_fifo(self, tile: DacTile) -> None:
        with self.__flock:
            self.__command.SetupFIFO(int(RfConverter.DAC), int(tile), 0)


    def _disable_adc_fifo(self, tile: AdcTile) -> None:
        with self.__flock:
            self.__command.SetupFIFO(int(RfConverter.ADC), int(tile), 0)


    def _enable_adc_calibration_adjustment(self, tile: AdcTile, channel: AdcChannel):
        with self.__flock:
            self.__command.ConfigureAdcCalibration(int(tile), int(channel), 0, 0)


    def _disable_adc_calibration_adjustment(self, tile: AdcTile, channel: AdcChannel):
        with self.__flock:
            self.__command.ConfigureAdcCalibration(int(tile), int(channel), 0, 1)


    def _is_adc_calibration_adjustment_enabled(self, tile: AdcTile, channel: AdcChannel):
        with self.__flock:
            (cal_frozen, disable_freeze_pin, freeze_calibration) = \
                self.__command.GetAdcCalibirationStatus(int(tile), int(channel))
            return not bool(cal_frozen)


    def __to_interrupt_mask(self, *flags: RfdcInterrupt) -> int:
        mask = 0
        for flag in flags:
            if flag == RfdcInterrupt.DAC_INTERPOLATION_OVERFLOW:
                mask |= RfdcIntrpMask.DAC_I_INTP_STG0_OVF
                mask |= RfdcIntrpMask.DAC_I_INTP_STG1_OVF
                mask |= RfdcIntrpMask.DAC_I_INTP_STG2_OVF
                mask |= RfdcIntrpMask.DAC_Q_INTP_STG0_OVF
                mask |= RfdcIntrpMask.DAC_Q_INTP_STG1_OVF
                mask |= RfdcIntrpMask.DAC_Q_INTP_STG2_OVF
            elif flag == RfdcInterrupt.DAC_QMC_GAIN_PHASE_OVERFLOW:
                mask |= RfdcIntrpMask.DAC_QMC_GAIN_PHASE_OVF
            elif flag == RfdcInterrupt.DAC_QMC_OFFSET_OVERFLOW:
                mask |= RfdcIntrpMask.DAC_QMC_OFFSET_OVF
            elif flag == RfdcInterrupt.DAC_INV_SINC_OVERFLOW:
                mask |= RfdcIntrpMask.DAC_INV_SINC_OVF
            elif flag == RfdcInterrupt.DAC_FIFO_OVERFLOW:
                mask |= RfdcIntrpMask.DAC_FIFO_OVF
            elif flag == RfdcInterrupt.DAC_FIFO_UNDERFLOW:
                mask |= RfdcIntrpMask.DAC_FIFO_UDF
            elif flag == RfdcInterrupt.DAC_FIFO_MARGINAL_OVERFLOW:
                mask |= RfdcIntrpMask.DAC_FIFO_MARGIANL_OVF
            elif flag == RfdcInterrupt.DAC_FIFO_MARGINAL_UNDERFLOW:
                mask |= RfdcIntrpMask.DAC_FIFO_MARGIANL_UDF
            elif flag == RfdcInterrupt.ADC_DECIMATION_OVERFLOW:
                mask |= RfdcIntrpMask.ADC_I_DMON_STG0_OVF
                mask |= RfdcIntrpMask.ADC_I_DMON_STG1_OVF
                mask |= RfdcIntrpMask.ADC_I_DMON_STG2_OVF
                mask |= RfdcIntrpMask.ADC_Q_DMON_STG0_OVF
                mask |= RfdcIntrpMask.ADC_Q_DMON_STG1_OVF
                mask |= RfdcIntrpMask.ADC_Q_DMON_STG2_OVF
            elif flag == RfdcInterrupt.ADC_QMC_GAIN_PHASE_OVERFLOW:
                mask |= RfdcIntrpMask.ADC_QMC_GAIN_PHASE_OVF
            elif flag == RfdcInterrupt.ADC_QMC_OFFSET_OVERFLOW:
                mask |= RfdcIntrpMask.ADC_QMC_OFFSET_OVF
            elif flag == RfdcInterrupt.SUB_ADC_OVER_RANGE:
                mask |= RfdcIntrpMask.SUB_ADC0_OVR
                mask |= RfdcIntrpMask.SUB_ADC0_UDR
                mask |= RfdcIntrpMask.SUB_ADC1_OVR
                mask |= RfdcIntrpMask.SUB_ADC1_UDR
                mask |= RfdcIntrpMask.SUB_ADC2_OVR
                mask |= RfdcIntrpMask.SUB_ADC2_UDR
                mask |= RfdcIntrpMask.SUB_ADC3_OVR
                mask |= RfdcIntrpMask.SUB_ADC3_UDR
            elif flag == RfdcInterrupt.ADC_OVER_VOLTAGE:
                mask |= RfdcIntrpMask.ADC_OVV
            elif flag == RfdcInterrupt.ADC_OVER_RANGE:
                mask |= RfdcIntrpMask.ADC_OVR
            elif flag == RfdcInterrupt.ADC_FIFO_OVERFLOW:
                mask |= RfdcIntrpMask.ADC_FIFO_OVF
            elif flag == RfdcInterrupt.ADC_FIFO_UNDERFLOW:
                mask |= RfdcIntrpMask.ADC_FIFO_UDF
            elif flag == RfdcInterrupt.ADC_FIFO_MARGINAL_OVERFLOW:
                mask |= RfdcIntrpMask.ADC_FIFO_MARGIANL_OVF
            elif flag == RfdcInterrupt.ADC_FIFO_MARGINAL_UNDERFLOW:
                mask |= RfdcIntrpMask.ADC_FIFO_MARGIANL_UDF

        return mask


    def __get_lock_dir(self) -> str:
        """
        ロックファイルを置くディレクトリを取得する.
        このディレクトリは環境変数 (E7AWG_HW_LOCKDIR) で指定され, アクセス権限は 777 でなければならない.
        環境変数がない場合は /usr/local/etc/e7awg_hw/lock となる.
        """
        dirpath = os.getenv('E7AWG_HW_LOCKDIR', '/usr/local/etc/e7awg_hw/lock')
        if not os.path.isdir(dirpath):
            err: OSError = FileNotFoundError(
                'Cannot find the directory for lock files.\n'
                "Create a directory '/usr/local/etc/e7awg_hw/lock' "
                "or set the E7AWG_HW_LOCKDIR environment variable to the path of another directory"
                ', and then set its permission to 777.')
            log_error(err, *self._loggers)
            raise err

        permission_flags = stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO  
        if (os.stat(dirpath).st_mode & permission_flags) != permission_flags:
            err = PermissionError(
                'Set the permission of the directory for lock files to 777.  ({})'.format(dirpath))
            log_error(err, *self._loggers)
            raise err
        
        return os.path.abspath(dirpath)
