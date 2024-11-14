from __future__ import annotations

from typing import cast
from typing_extensions import Self
from enum import IntEnum, Enum
from e7awgsw import E7AwgHwType

class DigitalOutTrigger(Enum):
    """ディジタル出力モジュールに入力されるトリガの種類"""

    # ディジタル出力モジュールが IDLE 状態のとき受け付ける
    # ディジタル値の出力を開始する.
    START = 0

    # ディジタル出力モジュールが PAUSE 状態のとき受け付ける.
    # ディジタル値の出力を最初から始める.
    RESTART = 1

    # ディジタル出力モジュールが ACTIVE 状態のとき受けつける.
    # PAUSE 状態へ移行し, ディジタル値の出力を一時中断する.
    # 出力値は PAUSE 状態に移行したときに出力していた値が保持される.
    PAUSE = 2

    # ディジタル出力モジュールが PAUSE 状態のとき受け付ける.
    # ACTIVE 状態に移行して, 波形の出力を PAUSE に遷移する前の状態から再開する.
    RESUME = 3


class DigitalOut(IntEnum):
    """ディジタル出力モジュールの ID"""
    U0 = 0
    U1 = 1
    U2 = 2
    U3 = 3
    U4 = 4
    U5 = 5
    U6 = 6
    U7 = 7
    U8 = 8
    U9 = 9
    U10 = 10
    U11 = 11
    U12 = 12
    U13 = 13
    U14 = 14
    U15 = 15
    U16 = 16
    U17 = 17
    U18 = 18
    U19 = 19
    U20 = 20
    U21 = 21
    U22 = 22
    U23 = 23
    U24 = 24
    U25 = 25
    U26 = 26
    U27 = 27
    U28 = 28
    U29 = 29
    U30 = 30
    U31 = 31
    U32 = 32
    U33 = 33

    @classmethod
    def on(cls, design_type: E7AwgHwType) -> set[Self]:
        """引数で指定した e7awg_hw デザインに含まれる全ての AWG の ID をセットに格納して返す"""
        if design_type == E7AwgHwType.ZCU111:
            return cast(set[Self], set(DigitalOut))

        return set()
