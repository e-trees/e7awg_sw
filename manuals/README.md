# e7awg_hw ユーザマニュアル

## 1. 機能概要
e7awg_hw は，ユーザが定義した波形データを出力する機能と，入力された波形データに信号処理を適用してメモリに保存する機能を備えた FPGA デザインです．FPGA 内部の各モジュールは，10G Ethernet で送られる UDP/IP パケットにて制御可能になっています．
以下に e7awg_hw の概略図を示します．

![FPGA ブロック図](./figures/fpga_block_diagram.png)

### 各モジュールとその機能
|  モジュール  |  機能  |
| ---- | ---- |
| HBM (High Bandwidth Memory) | 高速なオンチップメモリで，出力波形のサンプル値やキャプチャデータを保持します． |
| 10G/25G Ethernet Subsystem | 10GbE の物理層の信号とイーサネットフレームを相互に変換します． |
| e7udpip10G | UDP/IP に従って UDP パケットの送受信を行います． |
| upl axi rw | e7udpip10G と HBM 間のデータの送受信を制御します． |
| capture ctrl | e7udpip10G から送られるデータをもとに capture unit を制御します． |
| capture module | 複数の capture unit を束ねるモジュールです．同じ capture module の中の capture unit は全て同じ入力波形データを受け取ります．|
| capture unit | 入力波形データに信号処理を適用して HBM に格納します．|
| awg ctrl | e7udpip10G から送られるデータをもとに AWG を制御します． |
| AWG | HBM からサンプル値を読み出し，ユーザが定義した波形の並びで出力します． |
| jesd204 txrx if| jesd204c の規格に沿って capture module と ADC および AWG と DAC 間のデータ転送を行います． |


## 2. AWG ソフトウェアインタフェース仕様
  - 状態遷移図
  - 波形シーケンスの定義
  - メモリマップ
  - 波形パラメータの制約
  - UDP データフォーマット


## 3. キャプチャモジュールソフトウェアインタフェース仕様
  - 状態遷移図
  - キャプチャシーケンスの定義
  - メモリマップ
  - キャプチャパラメータ制約
  - UDP データフォーマット

## 4. HBM データレイアウト
