from __future__ import annotations
from enum import IntEnum
from ..zcu111.rfdcdefs import RfdcInterrupt as RfdcInterruptZ1

class DacTile(IntEnum):
    """DAC タイルの ID"""
    T0 = 0 #: Tile 228
    T1 = 1 #: Tile 229
    T2 = 2 #: Tile 230
    T3 = 3 #: Tile 231


class DacChannel(IntEnum):
    """DAC チャネルの ID"""
    C0 = 0
    C1 = 1
    C2 = 2
    C3 = 3


class RfdcInterrupt(IntEnum):
    """Rfdc 割り込み一覧"""
    # DAC 補間オーバーフロー
    DAC_INTERPOLATION_OVERFLOW = 0
    # ADC 間引きオーバーフロー
    ADC_DECIMATION_OVERFLOW = 1
    # QMC オーバーフロー
    DAC_QMC_GAIN_PHASE_OVERFLOW  = 2
    DAC_QMC_OFFSET_OVERFLOW      = 3
    ADC_QMC_GAIN_PHASE_OVERFLOW  = 4
    ADC_QMC_OFFSET_OVERFLOW      = 5
    # Inverse Sinc Filter オーバーフロー
    DAC_INV_SINC_OVERFLOW = 6
    # SUB ADC オーバーレンジ
    SUB_ADC_OVER_RANGE = 7
    # ADC オーバーボルテージ
    ADC_OVER_VOLTAGE = 8
    # ADC オーバーレンジ
    ADC_OVER_RANGE = 9
    # DAC FIFO オーバー/アンダーフロー
    DAC_FIFO_OVERFLOW  = 10
    DAC_FIFO_UNDERFLOW = 11
    DAC_FIFO_MARGINAL_OVERFLOW  = 12
    DAC_FIFO_MARGINAL_UNDERFLOW = 13
    # ADC FIFO オーバー/アンダーフロー
    ADC_FIFO_OVERFLOW  = 14
    ADC_FIFO_UNDERFLOW = 15
    ADC_FIFO_MARGINAL_OVERFLOW  = 16
    ADC_FIFO_MARGINAL_UNDERFLOW = 17
    # DAC I/Q ミキサオーバー/アンダーフロー
    DAC_MIXER_OVERFLOW_UNDERFLOW = 18
    # Image Rejection Block オーバーフロー
    DAC_IMAGE_REJECTION_OVERFLOW = 19

    @classmethod
    def to_msg(cls, interrupt: int) -> str:
        if interrupt == cls.DAC_MIXER_OVERFLOW_UNDERFLOW:
            return 'Overflow detected in DAC I/Q Mixer.'
        if interrupt == cls.DAC_IMAGE_REJECTION_OVERFLOW:
            return 'Overflow detected in DAC Imege Rejection Block.'
        
        return RfdcInterruptZ1.to_msg(interrupt)
