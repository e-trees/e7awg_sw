# AWG ユーザマニュアル

本資料は，ZCU111 を利用した Arbitrary Waveform Generator (以下 AWG) の利用者向けマニュアルです．

## 1. システム構成

AWG は ZCU111 の FPGA 上に実装されており，そのシステム構成は以下のようになります．
AWG の制御には専用の Python API を用います．
この API には Python で作成した波形データを FPGA に送信する機能や，AWG の動作完了を待つ機能などが含まれています．
本システムに含まれるディジタル出力モジュールの詳細は [こちら](./digital_output.md)  を参照してください．

<br>

**デザイン 0 , 1**

廃止しました．

<br>

**デザイン 2, 3**

![システムオーバービュー1](figures/awg_system_overview_1.png)

<br>

**デザイン 4**

![システムオーバービュー2](figures/awg_system_overview_2.png)

<br>

本システムには複数の AWG が含まれていますが，波形データ RAM の帯域の都合上，同時に動作可能な AWG の組み合わせには以下の制限があります．

| デザイン ID | 同時に動作可能な AWG の組み合わせ |
| --- | --- |
| 2 | AWG 0 ~ 5 の中から最大 5 つに加えて，AWG 6 と 7 の 2 つ |
| 3 | AWG 0 ~ 5 の中から最大 1 つに加えて，AWG 6 と 7 の 2 つ |
| 4 | AWG 0 ~ 3, 6, 7 の全て |

<br>

## 2. ZCU111 版 e7awg_hw の種類

ZCU111 上で動作する e7awg_hw には 3 種類の FPGA デザインがあります．
デザイン間で異なる部分は以下の通りです。

 - AWG のサンプリングレート
 - キャプチャユニット のサンプリングレート
 - データ RAM の構成

データ RAM は，波形データ RAM とキャプチャデータ RAM を合わせた RAM の呼び方です．

 <br>

| デザイン ID | AWG の<br>サンプリングレート [Msps] | キャプチャユニットの<br>サンプリングレート [Msps] | データ RAM の構成 |
| --- | --- | --- | --- | 
| 2 | 552.96 | 552.96 | AWG 0 ~ 5 → DRAM x1（512 MBytes / AWG） <br> AWG 6 → URAM x1（1280 KBytes） <br> AWG 7 → URAM x1（1280 KBytes） <br> キャプチャユニット 0 → BRAM x1 (320 KBytes) <br> キャプチャユニット 1 → BRAM x1 (320 KBytes) <br> キャプチャユニット 2 → BRAM x1 (320 KBytes) <br> キャプチャユニット 3 → BRAM x1 (320 KBytes) <br> キャプチャユニット 4 → BRAM x1 (320 KBytes) <br> キャプチャユニット 5 → BRAM x1 (320 KBytes) <br> キャプチャユニット 6 → BRAM x1 (320 KBytes) <br> キャプチャユニット 7 → BRAM x1 (320 KBytes)|
| 3 | 3256.32 | 3256.32 | AWG 0 ~ 5 → DRAM x1（512 MBytes / AWG） <br> AWG 6 → URAM x1（1280 KBytes） <br> AWG 7 → URAM x1（1280 KBytes） <br> キャプチャユニット 0 → BRAM x1 (320 KBytes) <br> キャプチャユニット 1 → BRAM x1 (320 KBytes) <br> キャプチャユニット 2 → BRAM x1 (320 KBytes) <br> キャプチャユニット 3 → BRAM x1 (320 KBytes) <br> キャプチャユニット 4 → BRAM x1 (320 KBytes) <br> キャプチャユニット 5 → BRAM x1 (320 KBytes) <br> キャプチャユニット 6 → BRAM x1 (320 KBytes) <br> キャプチャユニット 7 → BRAM x1 (320 KBytes) |
| 4 | 798.72 | 798.72 | AWG 0 ~ 3, 6 → DRAM x1 (512MBytes / AWG) <br> AWG 7 → URAM x1 (2560 KBytes) <br> キャプチャユニット 0 → BRAM x1 (256 KBytes) <br> キャプチャユニット 1 → BRAM x1 (256 KBytes) |

※ サンプリングレートは，I/Q データの場合 I データと Q データをまとめて 1 サンプルとして計算しています．

<br>

## 3. AWG の状態

AWG は下図の状態を持ち，特定の Python API (図中の青字) が呼ばれたときや HW の特定の動作によって遷移します.

![AWGの状態](figures/awg_state.png)

**状態の説明**

| 状態名 | 説明 |
| --- | --- |
| Idle | 初期状態. |
| Ready | 波形の出力準備が終わって外部スタートトリガの入力を待っている状態です. |
| Active | ユーザ定義波形を出力します．|
| Pause | ユーザ定義波形の出力を一時停止します．<br> 停止中に AWG から出力されるサンプル値は I データ, Q データ共に 0 です．|

<br>

## 4. 出力波形の構造

AWG が出力可能な波形の構造と制約について説明します．

ユーザが各 AWG に対して設定した出力波形全体を**ユーザ定義波形**と言います．
**ユーザ定義波形**は **wait word** と，その後に続く**波形シーケンス**の繰り返しで構成されます．
**波形シーケンス**は，最大 4294967295 回繰り返すことが可能です．
**wait word** は無くても問題ありません．

![user_def_wave](../hw/figures/user_def_wave.png)

**wait word** は, I，Q 共に値が 0 のサンプルが並んだ波形です．
8 サンプルを 1 つの単位とする **AWG ワード**単位で指定可能で，最大長は 4294967295 **AWG ワード**となります

![wait_word](../hw/figures/wait_word.png)

**波形シーケンス**は**波形チャンク**の繰り返しを並べたもので構成されます．
**波形チャンク**は最大 16 個まで定義でき，各チャンクは 4294967295 回まで繰り返すことが可能です．

![wave_seq](../hw/figures/wave_seq.png)

**波形チャンク**は**波形パート**と**ポストブランク**で構成されます．
**ポストブランク**は無くても問題ありません．

![wave_chunk](../hw/figures/wave_chunk.png)


**波形パート**は任意の値のサンプルが並んでおり，そのサンプル数はデザイン 2 と 3 では **512**，デザイン 4 では **2048** の倍数でなければなりません．

![wave_part](../hw/figures/wave_part.png)

また，波形パートのサンプル数は波形データ RAM の容量の都合上，以下の制約も満たさなければなりません． 

![wave part constraint](../hw/figures/wave_part_constraint.png)

<!--
$$
\begin{align*}
S_u &\stackrel{\mathrm{def}}{=} \rm{AWG}\,u\, が出力する波形シーケンス \\[1ex]
N_u &: S_u で定義された波形チャンクの数  \\[1ex]
W_u(i) &: S_u の波形チャンク \; i \;の波形パートのサンプル数 \\[1ex]
L_u &: \rm{AWG}\,u\, の波形データ格納領域に格納可能な総サンプル数 \\[1ex]
[制約] \;\; &\displaystyle \sum_{i=0}^{N_u-1} W_u(i) \leqq L_u \\[5ex]

\langle デザイン 2, 3 \rangle \\[1ex]
L_u &= \left\{
\begin{array}{ll}
  134217728\;\; & (u \in \{0, 1, 2, 3, 4, 5\}) \\[1ex]
  327680\;\; & (u \in \{6, 7\}) \\[1ex]
\end{array} \\
\right.\\

\\

\langle デザイン 4 \rangle \\[1ex]
L_u &= \left\{
\begin{array}{ll}
  134217728\;\; & (u \in \{0, 1, 2, 3, 6\}) \\[1ex]
  655360\;\; & (u \in \{7\}) \\[1ex]
\end{array} \\
\right.\\

\end{align*}
$$
-->

<br>

ポストブランクは値が 0 のサンプルが並んだ波形です．
8 サンプルを 1 つの単位とする AWG ワード単位で指定可能で，最大長は 4294967295 AWG ワードとなります．

![post blank](../hw/figures/post_blank.png)


## 5. DAC パラメータ

RF Data Converter の DAC は以下のパラメータで固定となっており，ユーザが変更することはできません．

**デザイン 2**
- サンプリングレート : 1105.92 [Msps]
- I/Q ミキサ : 有効
- インタポレーション : 2倍

<br>

**デザイン 3**
- サンプリングレート : 6512.64 [Msps]
- I/Q ミキサ : 有効
- インタポレーション : 2倍

<br>

**デザイン 4**
- サンプリングレート : 1597.44 [Msps]
- I/Q ミキサ : 有効
- インタポレーション : 2倍

<br>

AWG から出力される **ユーザ定義波形** は，DAC 内部でサンプル数が 2 倍になる様に補間された後，DAC のサンプリングレートで出力されます．
よって，例えばデザイン 3 では，サンプル数が 512 * n 個 (n = 1, 2, 3, ... ) の **波形パート** は，長さが 157.233 * n [ns] (≒ 2 * 512 * n / 6512.64 * 1000) の波形となって出力されます．

## 6. AWG 制御用 API の詳細

本章では AWG の操作に必要な Python API を手順ごとに説明します．
各 API の詳細は, 関数ヘッダコメントを参照してください.

### 6.1. RF Data Converter の DAC タイルと DAC タイル ID の対応関係

本 API には RF Data Convnerter の DAC タイルを指定して実行するメソッドがあります．
各タイルに対応する ID は e7awgsw.zcu111 パッケージの DacTile クラスに列挙子として定義されており，その対応関係は以下の通りです．

| DAC タイル | DAC タイル ID | 列挙子の値 |
| -- | -- | -- |
| Tile 228 | T0 | 0 |
| Tile 229 | T1 | 1 |

<br>

### 6.2. AWG と DAC の初期化

AWG と DAC は，次節以降で述べる操作を行う前に必ず初期化しなければなりません．
DAC の初期化は，最初に RfdcCtrl クラスの set_dac_mixer_settings で I/Q ミキサの設定を行った後，
同クラスの sync_dac_tiles または sync_dac_adc_tiles メソッドでタイルの同期を行います．
AWG の初期化には AwgCtrl クラスの initialize メソッドを使用します．

初期化のコード例を以下に示します

```
import e7awgsw as e7s
import e7awgsw.zcu111 as e7sz

zcu111_ip_addr = '192.168.1.3' # ZCU111 の 10/100/1000 Mb Ethernet ポートの IP アドレス
fpga_ip_addr = '10.0.0.16'     # ZCU111 の 10 Gb Ethernet ポートの IP アドレス

# DAC/AWG 制御用オブジェクトを作成する    
with (e7sz.RftoolTransceiver(zcu111_ip_addr, 15) as trasnceiver,
      e7sz.RfdcCtrl(trasnceiver, e7s.E7AwgHwType.ZCU111_URAM_X2) as rfdc_ctrl,
      e7s.AwgCtrl(fpga_ip_addr, e7s.E7AwgHwType.ZCU111_URAM_X2) as awg_ctrl):

    # FPGA コンフィギュレーション
    e7sz.configure_fpga(trasnceiver, e7s.E7AwgHwType.ZCU111_URAM_X2)

    for tile_id in list(e7sz.DacTile):
        for channel_id in list(e7sz.DacChannel):
            # I/Q ミキサの設定
            rfdc_ctrl.set_dac_mixer_settings(
                tile = tile_id,                # タイル ID
                channel = channel_id,          # チャネル ID
                freq = 100,                    # 周波数 (MHz)
                phase = 0,                     # 初期位相 (degrees)
                scale =  e7sz.MixerScale.V0P7) # 振幅

    # DAC タイルを同期させる.
    rfdc_ctrl.sync_dac_tiles()

    # AWG 0 , AWG 3 を初期化
    awg_ctrl.initialize(e7s.AWG.U0, e7s.AWG.U3)
```

### 6.3. 波形データの設定

AWG に設定する波形データは，e7awgsw パッケージの WaveSequence クラスを用いて作成します．
4 章で説明したユーザ定義波形の

- 波形シーケンスの繰り返し回数
- wait word の長さ

をコンストラクタで指定し

- 波形パートのサンプル値
- 波形チャンクの繰り返し回数
- ポストブランク長

を add_chunk メソッドで指定します．

波形データを作成するコードの例を以下に示します．

```
import e7awgsw as e7s

wave_seq = e7s.WaveSequence(
    num_wait_words = 10,  # wait word の AWG ワード数
    num_seq_repeats = 2,  # 波形シーケンスの繰り返し回数
    e7s.E7AwgHwType.ZCU111_URAM_X2)  


# 波形チャンク 0 の定義
samples_0 = [(1, 2), ..., (100, 200)]  # [(I0, Q0), (I1, Q1), ...]
wave_seq.add_chunk(
    iq_samples = samples_0,  # サンプル値のリスト
    num_blank_words = 0,     # ポストブランクの AWG ワード数
    num_repeats = 1)         # 波形チャンクの繰り返し回数

# 波形チャンク 1 の定義
samples_1 = [(-1, -2), ..., (-100, -200)]  # [(I0, Q0), (I1, Q1), ...]
wave_seq.add_chunk(
    iq_samples = samples_1,  # サンプル値のリスト
    num_blank_words = 3,     # ポストブランクの AWG ワード数
    num_repeats = 2)         # 波形チャンクの繰り返し回数
```

上記のコードで定義されるユーザ定義波形は以下のようになります.

![user define wave](figures/user_defined_wave.png)

定義した波形を AWG に設定するには AwgCtrl クラスの set_wave_sequence メソッドを使用します．

波形データを設定するコードの例を以下に示します．

```
import e7awgsw as e7s
import e7awgsw.zcu111 as e7sz

zcu111_ip_addr = '192.168.1.3' # ZCU111 の 10/100/1000 Mb Ethernet ポートの IP アドレス
fpga_ip_addr = '10.0.0.16'     # ZCU111 の 10 Gb Ethernet ポートの IP アドレス

# DAC/AWG 制御用オブジェクトを作成する
with (e7sz.RftoolTransceiver(zcu111_ip_addr, 15) as trasnceiver,
      e7sz.RfdcCtrl(trasnceiver, e7s.E7AwgHwType.ZCU111_URAM_X2) as rfdc_ctrl,
      e7s.AwgCtrl(fpga_ip_addr, e7s.E7AwgHwType.ZCU111_URAM_X2) as awg_ctrl):

    ### AWG / DAC 初期化 (省略) ###
    ### 波形データの定義 (省略) ###

    # AWG 0 , AWG 3 に波形データを設定
    awg_ctrl.set_wave_sequence(e7s.AWG.U0, wave_seq)
    awg_ctrl.set_wave_sequence(e7s.AWG.U3, wave_seq)
```

### 6.4. 波形の出力開始と完了待ち

AWG の波形出力を開始するには AwgCtrl クラスの start_awgs メソッドを使用します．
このメソッドで指定した全ての AWG は同時にユーザ定義波形の出力を開始します．
AWG の波形出力が完了するのを待つには AwgCtrl クラスの wait_for_awgs_to_stop メソッドを使用します．
このメソッドは指定した全ての AWG の波形出力が完了するか，タイムアウトまでコントロールを返しません．

波形の出力開始と完了待ちを行うコードの例を以下に示します．

```
import e7awgsw as e7s
import e7awgsw.zcu111 as e7sz

zcu111_ip_addr = '192.168.1.3' # ZCU111 の 10/100/1000 Mb Ethernet ポートの IP アドレス
fpga_ip_addr = '10.0.0.16'     # ZCU111 の 10 Gb Ethernet ポートの IP アドレス

# DAC/AWG 制御用オブジェクトを作成する
with (e7sz.RftoolTransceiver(zcu111_ip_addr, 15) as trasnceiver,
      e7sz.RfdcCtrl(trasnceiver, e7s.E7AwgHwType.ZCU111_URAM_X2) as rfdc_ctrl,
      e7s.AwgCtrl(fpga_ip_addr, e7s.E7AwgHwType.ZCU111_URAM_X2) as awg_ctrl):

    ### AWG / DAC 初期化 (省略) ###
    ### 波形データの定義 (省略) ###
    ### 波形データの設定 (省略) ###
    
    # AWG 0 と AWG 3 のユーザ定義波形出力スタート
    awg_ctrl.start_awgs(e7s.AWG.U0, e7s.AWG.U3)
    
    # タイムアウト 5 秒で AWG 0 と AWG 3 の波形出力完了待ち
    awg_ctrl.wait_for_awgs_to_stop(5, e7s.AWG.U0, e7s.AWG.U3)
```

### 6.5. 波形出力の一時停止

ユーザ定義波形の出力を一時停止するには AwgCtrl クラスの pause_awgs メソッドを使用します．
このメソッドで指定した全ての AWG は同時にユーザ定義波形の出力を一時停止します．

ユーザ定義波形の出力を一時停止するコードの例を以下に示します．

```
import e7awgsw as e7s
import e7awgsw.zcu111 as e7sz

zcu111_ip_addr = '192.168.1.3' # ZCU111 の 10/100/1000 Mb Ethernet ポートの IP アドレス
fpga_ip_addr = '10.0.0.16'     # ZCU111 の 10 Gb Ethernet ポートの IP アドレス

# DAC/AWG 制御用オブジェクトを作成する
with (e7sz.RftoolTransceiver(zcu111_ip_addr, 15) as trasnceiver,
      e7sz.RfdcCtrl(trasnceiver, e7s.E7AwgHwType.ZCU111_URAM_X2) as rfdc_ctrl,
      e7s.AwgCtrl(fpga_ip_addr, e7s.E7AwgHwType.ZCU111_URAM_X2) as awg_ctrl):

    ### AWG / DAC 初期化 (省略) ###
    ### 波形データの定義 (省略) ###
    ### 波形データの設定 (省略) ###
    ### AWG の波形出力スタート (省略) ###
    
    # AWG 0 と AWG 3 のユーザ定義波形の出力を一時停止
    awg_ctrl.pause_awgs(e7s.AWG.U0, e7s.AWG.U3)
```

### 6.6. 波形出力の再開

ユーザ定義波形の出力を再開するには AwgCtrl クラスの resume_awgs メソッドを使用します．
このメソッドで指定した全ての AWG は同時にユーザ定義波形の出力を再開します．

ユーザ定義波形の出力を再開するコードの例を以下に示します．

```
import e7awgsw as e7s
import e7awgsw.zcu111 as e7sz

zcu111_ip_addr = '192.168.1.3' # ZCU111 の 10/100/1000 Mb Ethernet ポートの IP アドレス
fpga_ip_addr = '10.0.0.16'     # ZCU111 の 10 Gb Ethernet ポートの IP アドレス

# DAC/AWG 制御用オブジェクトを作成する
with (e7sz.RftoolTransceiver(zcu111_ip_addr, 15) as trasnceiver,
      e7sz.RfdcCtrl(trasnceiver, e7s.E7AwgHwType.ZCU111_URAM_X2) as rfdc_ctrl,
      e7s.AwgCtrl(fpga_ip_addr, e7s.E7AwgHwType.ZCU111_URAM_X2) as awg_ctrl):

    ### AWG / DAC 初期化 (省略) ###
    ### 波形データの定義 (省略) ###
    ### 波形データの設定 (省略) ###
    ### AWG の波形出力スタート (省略) ###

    # AWG 0 と AWG 3 のユーザ定義波形の出力を一時停止
    awg_ctrl.pause_awgs(e7s.AWG.U0, e7s.AWG.U3)

    time.sleep(2)

    # AWG 0 と AWG 3 のユーザ定義波形の出力を再開
    awg_ctrl.resume_awgs(e7s.AWG.U0, e7s.AWG.U3)
```

### 6.7. 外部トリガの有効化

AWG が外部スタートトリガを受け付ける状態にした後で，PMOD 1 の P0 を Lo から Hi にすると AWG の波形出力を開始することができます.

![pmod_ports](figures/pmod_ports_0.png)

AWG の外部スタートトリガを有効にするコード例を以下に示します．

```
import e7awgsw as e7s
import e7awgsw.zcu111 as e7sz

zcu111_ip_addr = '192.168.1.3' # ZCU111 の 10/100/1000 Mb Ethernet ポートの IP アドレス
fpga_ip_addr = '10.0.0.16'     # ZCU111 の 10 Gb Ethernet ポートの IP アドレス

# DAC/AWG 制御用オブジェクトを作成する
with (e7sz.RftoolTransceiver(zcu111_ip_addr, 15) as trasnceiver,
      e7sz.RfdcCtrl(trasnceiver, e7s.E7AwgHwType.ZCU111_URAM_X2) as rfdc_ctrl,
      e7s.AwgCtrl(fpga_ip_addr, e7s.E7AwgHwType.ZCU111_URAM_X2) as awg_ctrl):

    ### AWG / DAC 初期化 (省略) ###
    ### 波形データの定義 (省略) ###
    ### 波形データの設定 (省略) ###

    # AWG 0 と AWG 3 を外部トリガを受け付ける状態にする.
    awg_ctrl.prepare_awgs(e7s.AWG.U0, e7s.AWG.U3)

    # 以降 PMOD 1 の P0 が Lo から Hi に変化すると AWG 0 と AWG 3 は波形の出力を開始する.
```
