
# ---- AWG ----
# 波形レジストリの最大エントリ数
MAX_WAVE_REGISTRY_ENTRIES = 512
# 波形 RAM のワードサイズ (bytes)
WAVE_RAM_WORD_SIZE = 32

# ---- Capture Unit ----
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
SEQUENCER_REG_PORT = 0x4000
SEQUENCER_CMD_PORT = 0x4000
