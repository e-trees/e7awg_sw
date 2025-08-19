from __future__ import annotations

from enum import IntEnum

class RfConverter(IntEnum):
    ADC = 0
    DAC = 1


class MixerScale(IntEnum):
    """I/Q ミキサの振幅"""
    # Real -> I/Q なら x1, それ以外なら x0.7
    # 参考 : https://xilinx.github.io/embeddedsw.github.io/rfdc/doc/html/api/group___overview.html
    AUTO = 0
    # x1
    V1P0 = 1
    # x0.7
    V0P7 = 2
    

class RfdcIntrpMask(IntEnum):
    """Rfdc 割り込みマスク一覧"""
    # DAC 補間オーバーフロー
    DAC_I_INTP_STG0_OVF       = 0x00000010
    DAC_I_INTP_STG1_OVF       = 0x00000020
    DAC_I_INTP_STG2_OVF       = 0x00000040
    DAC_I_INTP_STG3_OVF       = 0x00010000 # Gen3/DFE
    DAC_Q_INTP_STG0_OVF       = 0x00000080
    DAC_Q_INTP_STG1_OVF       = 0x00000100
    DAC_Q_INTP_STG2_OVF       = 0x00000200
    DAC_Q_INTP_STG3_OVF       = 0x00020000 # Gen3/DFE
    # ADC 間引きオーバーフロー
    ADC_I_DMON_STG0_OVF       = 0x00000010
    ADC_I_DMON_STG1_OVF       = 0x00000020
    ADC_I_DMON_STG2_OVF       = 0x00000040
    ADC_Q_DMON_STG0_OVF       = 0x00000080
    ADC_Q_DMON_STG1_OVF       = 0x00000100
    ADC_Q_DMON_STG2_OVF       = 0x00000200
    # QMC オーバーフロー
    DAC_QMC_GAIN_PHASE_OVF    = 0x00000400
    DAC_QMC_OFFSET_OVF        = 0x00000800
    ADC_QMC_GAIN_PHASE_OVF    = 0x00000400
    ADC_QMC_OFFSET_OVF        = 0x00000800
    # Inverse Sinc Filter オーバーフロー
    DAC_INV_SINC_OVF          = 0x00001000
    # Inverse Sinc Filter オーバーフロー  (Even Nyquist Zone)
    DAC_INV_SINC_EVEN_NYQ_OVF = 0x00080000 # Gen3/DFE
    # SUB ADC オーバーレンジ
    SUB_ADC0_OVR              = 0x00010000
    SUB_ADC0_UDR              = 0x00020000
    SUB_ADC1_OVR              = 0x00040000
    SUB_ADC1_UDR              = 0x00080000
    SUB_ADC2_OVR              = 0x00100000
    SUB_ADC2_UDR              = 0x00200000
    SUB_ADC3_OVR              = 0x00400000
    SUB_ADC3_UDR              = 0x00800000
    # ADC オーバーボルテージ
    ADC_OVV                   = 0x04000000
    # ADC オーバーレンジ
    ADC_OVR                   = 0x08000000
    # ADC common-mode オーバーレンジ
    ADC_COMMON_MODE_OVR       = 0x10000000 # Gen3/DFE
    ADC_COMMON_MODE_UDR       = 0x20000000 # Gen3/DFE
    # DAC FIFO オーバー/アンダーフロー
    DAC_FIFO_OVF              = 0x00000001
    DAC_FIFO_UDF              = 0x00000002
    DAC_FIFO_MARGIANL_OVF     = 0x00000004
    DAC_FIFO_MARGIANL_UDF     = 0x00000008
    # ADC FIFO オーバー/アンダーフロー
    ADC_FIFO_OVF              = 0x00000001
    ADC_FIFO_UDF              = 0x00000002
    ADC_FIFO_MARGIANL_OVF     = 0x00000004
    ADC_FIFO_MARGIANL_UDF     = 0x00000008
    # DAC I/Q ミキサ I 相オーバー/アンダーフロー
    DAC_MIXER_I_OVF_UDF       = 0x00002000 # Gen3/DFE
    # DAC I/Q ミキサ Q 相オーバー/アンダーフロー
    DAC_MIXER_Q_OVF_UDF       = 0x00004000 # Gen3/DFE
    # Image Rejection Block オーバーフロー
    DAC_IMR_OVF               = 0x00040000 # Gen3/DFE
