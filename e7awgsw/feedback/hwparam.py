
# ---- AWG ----
# AWG から出力するサンプルのサイズ (単位 : bytes,  I = 16 bit,  Q = 16 bit)
WAVE_SAMPLE_SIZE = 4
# AWG から 1 サイクルで出力されるデータのサイズ (bytes)
AWG_WORD_SIZE = 16
# AWG から 1 サイクルで出力されるデータのサンプル数
NUM_SAMPLES_IN_AWG_WORD = AWG_WORD_SIZE // WAVE_SAMPLE_SIZE
# 1 波形ブロックに含まれるサンプル数
NUM_SAMPLES_IN_WAVE_BLOCK = NUM_SAMPLES_IN_AWG_WORD * 16
# 波形レジストリの最大エントリ数
MAX_WAVE_REGISTRY_ENTRIES = 512
# 波形 RAM のワードサイズ (bytes)
WAVE_RAM_WORD_SIZE = 32

# ---- Capture Unit ----
# キャプチャユニットが 1 サイクルで取得するデータのサイズ (bytes)
ADC_WORD_SIZE = 16
# キャプチャユニットが取得するサンプルのサイズ (単位 : bytes,  I = 16 bit,  Q = 16 bit)
ADC_SAMPLE_SIZE = 4
# キャプチャユニットが 1 サイクルで取得するサンプル数
NUM_SAMPLES_IN_ADC_WORD = ADC_WORD_SIZE // ADC_SAMPLE_SIZE
# メモリに保存されたサンプルのサイズ (単位 : bytes,  I = 32 bit,  Q = 32 bit)
CAPTURED_SAMPLE_SIZE = 8
# メモリに保存された四値化結果のサイズ (bits)
CLASSIFICATION_RESULT_SIZE = 2
# 1 キャプチャユニットが保存可能なデータサイズ (bytes)
MAX_CAPTURE_SIZE = 256 * 1024 * 1024
# 積算ユニットが保持できる積算値の最大数
MAX_INTEG_VEC_ELEMS = 4096
# キャプチャ RAM のワードサイズ (bytes)
CAPTURE_RAM_WORD_SIZE = 32
# キャプチャデータをキャプチャ RAM に格納する際のアライメントサイズ (bytes)
CAPTURE_DATA_ALIGNMENT_SIZE = CAPTURE_RAM_WORD_SIZE * 16
# 波形レジストリの最大エントリ数
MAX_CAPTURE_PARAM_REGISTRY_ENTRIES = 512
# キャプチャ RAM 1 ワード当たりに含まれるサンプルの数
NUM_SAMPLES_IN_CAP_RAM_WORD = CAPTURE_RAM_WORD_SIZE // CAPTURED_SAMPLE_SIZE
# キャプチャ RAM 1 ワード当たりに含まれる四値化結果の数
NUM_CLS_RESULTS_IN_CAP_RAM_WORD = CAPTURE_RAM_WORD_SIZE * 8 // CLASSIFICATION_RESULT_SIZE

# ---- Sequencer ----
# コマンドエラーのサイズ (bytes)
CMD_ERR_REPORT_SIZE = 16 

#UDP ポート番号
WAVE_RAM_PORT = 0x4000
AWG_REG_PORT = 0x4001
CAPTURE_REG_PORT = 0x4001
SEQUENCER_REG_PORT = 0x4000
SEQUENCER_CMD_PORT = 0x4000
