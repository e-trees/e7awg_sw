from __future__ import annotations
from enum import IntEnum

class DacTile(IntEnum):
    """DAC タイルの ID"""
    T0 = 0 #: Tile 228
    T1 = 1 #: Tile 229

class AdcTile(IntEnum):
    """ADC タイルの ID"""
    T0 = 0 #: Tile 224
    T1 = 1 #: Tile 225
    T2 = 2 #: Tile 226
    T3 = 3 #: Tile 227

class DacChannel(IntEnum):
    """DAC チャネルの ID"""
    C0 = 0
    C1 = 1
    C2 = 2
    C3 = 3


class AdcChannel(IntEnum):
    """ADC チャネルの ID"""
    C0 = 0
    C1 = 1


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

    @classmethod
    def to_msg(cls, interrupt: int) -> str:
        if interrupt == cls.DAC_INTERPOLATION_OVERFLOW:
            return 'Overflow detected in DAC Interpolation Stage Datapath.'
        if interrupt == cls.ADC_DECIMATION_OVERFLOW:
            return 'Overflow detected in ADC Decimation Stage Datapath.'
        if interrupt == cls.DAC_QMC_GAIN_PHASE_OVERFLOW:
            return 'Overflow detected in DAC QMC Gain/Phase.'
        if interrupt == cls.DAC_QMC_OFFSET_OVERFLOW: 
            return 'Overflow detected in DAC QMC Offset.'
        if interrupt == cls.ADC_QMC_GAIN_PHASE_OVERFLOW:
            return 'Overflow detected in ADC QMC Gain/Phase.'
        if interrupt == cls.ADC_QMC_OFFSET_OVERFLOW:
            return 'Overflow detected in ADC QMC Offset.'
        if interrupt == cls.DAC_INV_SINC_OVERFLOW:
            return 'Overflow detected in DAC Inverse Sinc Filter.'
        if interrupt == cls.SUB_ADC_OVER_RANGE:
            return 'Sub ADC over/under range detected.'
        if interrupt == cls.ADC_OVER_VOLTAGE:
            return 'ADC over voltage detected.'
        if interrupt == cls.ADC_OVER_RANGE:
            return 'ADC over range detected.'
        if interrupt == cls.DAC_FIFO_OVERFLOW:
            return 'DAC FIFO overflow detected.'
        if interrupt == cls.DAC_FIFO_UNDERFLOW:
            return 'DAC FIFO underflow detected.'
        if interrupt == cls.DAC_FIFO_MARGINAL_OVERFLOW:
            return 'DAC FIFO marginal overflow detected.'
        if interrupt == cls.DAC_FIFO_MARGINAL_UNDERFLOW:
            return 'DAC FIFO marginal underflow detected.'
        if interrupt == cls.ADC_FIFO_OVERFLOW:
            return 'ADC FIFO overflow detected.'
        if interrupt == cls.ADC_FIFO_UNDERFLOW:
            return 'ADC FIFO underflow detected.'
        if interrupt == cls.ADC_FIFO_MARGINAL_OVERFLOW:
            return 'ADC FIFO marginal overflow detected.'
        if interrupt == cls.ADC_FIFO_MARGINAL_UNDERFLOW:
            return 'ADC FIFO marginal underflow detected.'
        
        raise ValueError('unknown rfdc interrupt {}'.format(interrupt))
