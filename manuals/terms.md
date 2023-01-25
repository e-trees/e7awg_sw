# 用語集

### 波形パラメータ

ユーザ定義波形の構成を決める以下のパラメータの総称です．
各要素の詳細は [e7awg_hw ユーザマニュアル](https://github.com/e-trees/e7awg_sw/tree/main/manuals) の **AWG 制御レジスタ一覧** の同名のレジスタの説明を参照してください．

- WAIT ワード数
- 波形シーケンスリピート回数
- チャンク数
- 波形送信可能ブロック周期
- 波形パートアドレス
- 波形パートワード数
- ポストブランクワード数
- チャンクリピート回数

<br>

### キャプチャパラメータ

キャプチャ区間の構成を決める以下のパラメータの総称です．
各要素の詳細は [e7awg_hw ユーザマニュアル](https://github.com/e-trees/e7awg_sw/tree/main/manuals) の **キャプチャ制御レジスタ一覧** の同名のレジスタの説明を参照してください．

- 信号処理モジュール有効/無効
- キャプチャディレイ
- キャプチャアドレス
- 積算区間数
- 総和区間数
- 総和開始点
- 総和終了点
- 総和区間 0~4095 の長さ
- 総和区間 0~4095 のポストブランク
- 複素 FIR の実数成分係数 0~15
- 複素 FIR の虚数成分係数 0~15
- I データ用 実数 FIR の係数 0~7
- Q データ用 実数 FIR の係数 0~7
- 複素窓関数の実数成分係数 0~2047
- 複素窓関数の虚数成分係数 0~2047
- 四値化判定式パラメータ a0, b0, c0, a1, b1, c1

<br>

### シーケンサ制御パケット

サーバから [sequencer](https://github.com/e-trees/e7awg_hw/blob/master/manuals/modules/sequencer.md) モジュールを制御するためのパケットです．
サーバが送受信する際のパケットフォーマットは [フィードバックシステムユーザマニュアル](https://github.com/e-trees/e7awg_sw/blob/main/manuals/feedback.md) の **シーケンサ制御パケットフォーマット** を参照してください．
sequencer が送受信する際のパケットフォーマットは [UPL パケット一覧](https://github.com/e-trees/e7awg_hw/blob/master/manuals/upl_packets.md) の **シーケンサ制御 UPL パケット** を参照してください．

<br>

### フィードバック制御コマンド

[フィードバックシステム](https://github.com/e-trees/e7awg_sw/blob/main/manuals/feedback.md)を制御するためのコマンドです．
シーケンサ制御パケットに格納されてサーバから [sequencer](https://github.com/e-trees/e7awg_hw/blob/master/manuals/modules/sequencer.md) へと送信されます．
各コマンドの詳細は，[フィードバックシステムユーザマニュアル](https://github.com/e-trees/e7awg_sw/blob/main/manuals/feedback.md) の **フィードバック制御コマンド** を参照してください．

<br>

### AWG シーケンサ制御パケット

サーバから [awg_sequencer](https://github.com/e-trees/e7awg_hw/blob/master/manuals/modules/awg_sequencer.md) モジュールを制御するためのパケットです．
サーバが送受信する際のパケットフォーマットは [AWG シーケンサユーザーマニュアル](https://github.com/e-trees/e7awg_sw/blob/simple_multi/manuals/sequencer.md) の **シーケンサ制御パケットフォーマット** を参照してください．
awg_sequencer が送受信する際のパケットフォーマットは [UPL パケット一覧](https://github.com/e-trees/e7awg_hw/blob/master/manuals/upl_packets.md) の **AWG シーケンサ制御パケット** を参照してください．

<br>

### AWG シーケンサコマンド

[awg_sequencer](https://github.com/e-trees/e7awg_hw/blob/master/manuals/modules/awg_sequencer.md) および e7awg_hw を制御するためのコマンドです．
AWG シーケンサ制御パケットに格納されて，サーバから awg_sequencer へと送信されます．
各コマンドの詳細は，[AWG シーケンサユーザーマニュアル](https://github.com/e-trees/e7awg_sw/blob/simple_multi/manuals/sequencer.md) の **AWG シーケンサコマンド説明** を参照してください．

<br>

### AWG シーケンサリクエスト

[awg_sequencer](https://github.com/e-trees/e7awg_hw/blob/master/manuals/modules/awg_seｓquencer.md) が処理するリクエストです．AWG シーケンサコマンドとは異なり，awg_sequencer に到着次第すぐに処理されます．
AWG シーケンサ制御パケットに格納されて，サーバから awg_sequencer へと送信されます．
各リクエストの詳細は，[AWG シーケンサユーザーマニュアル](https://github.com/e-trees/e7awg_sw/blob/simple_multi/manuals/sequencer.md) の **AWG シーケンサリクエスト説明** を参照してください．
