from __future__ import annotations

from typing import cast
from abc import ABCMeta, abstractmethod
from typing_extensions import Self
from ..hwdefs import E7AwgHwType

class DigitalOutParams(object, metaclass = ABCMeta):
    """各種デザインのディジタル出力モジュールに関連するパラメータを取得するためのインタフェースを規定するクラス."""

    @classmethod
    def of(self, design_type: E7AwgHwType) -> Self:
        if design_type == E7AwgHwType.ZCU111:
            return cast(Self, DigitalOutParamsZcu111())
               
        raise ValueError('Invalid e7awg_hw type.  ({})'.format(design_type))

    @abstractmethod
    def max_patterns(self) -> int:
        """ディジタル出力モジュールに設定可能な最大パターン数"""
        pass

    @abstractmethod
    def min_time(self) -> int:
        """ビットパターンの出力時間として設定可能な最小値"""
        pass

    @abstractmethod
    def max_time(self) -> int:
        """ビットパターンの出力時間として設定可能な最大値"""
        pass

    @abstractmethod
    def udp_port(self) -> int:
        """ディジタル出力モジュール制御レジスタにアクセスする際に使用する UDP ポート番号"""
        pass


class DigitalOutParamsZcu111(DigitalOutParams):
    """ZCU111 デザインのディジタル出力モジュールのパラメータを保持するクラス"""
    
    def max_patterns(self) -> int:
        return 512

    def min_time(self) -> int:
        return 2

    def max_time(self) -> int:
        return 0xFFFF_FFFF

    def udp_port(self) -> int:
        return 0x4001
