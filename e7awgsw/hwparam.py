from typing import Final

# ---- AWG ----
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

#UDP ポート番号
WAVE_RAM_PORT: Final = 0x4000
AWG_REG_PORT: Final = 0x4001
CAPTURE_REG_PORT: Final = 0x4001
