# AWG の一時停止と再開を行う

[awg_pause.py](./awg_pause.py) は AWG (Arbitrary Waveform Generator) の波形出力の「一時停止」と「再開」機能を確認するスクリプトです．
本スクリプトは ZCU111 版 e7awg_hw の `デザイン 0 ~ 2` に対応しています．
各デザインのモジュール構成については，[e7awg_hw ユーザマニュアル](../../../manuals/zcu111/hw/README.md) を参照してください．

本スクリプトで動作する AWG と上述のデザインの対応関係は以下の表の通りです．

| デザイン ID | AWG |
| --- | --- |
| 0 | 0 ~ 4 |
| 1 | 0 |
| 2 | 0 ~ 4，6 ~ 7 |
| 3 | 0, 6, 7 |

## セットアップ

DAC, PMOD とオシロスコープを接続します．

![セットアップ](./images/awg_x1_setup.png)

## 実行手順と結果

以下のコマンドを実行します．

```
# デザイン 0 を使用する場合
python awg_pause.py

# デザイン 1 を使用する場合
python awg_pause.py --design-type=dac6g

# デザイン 2 を使用する場合
python awg_pause.py --design-type=dac1g-uram2

# デザイン 3 を使用する場合
python awg_pause.py --design-type=dac6g-uram2
```

AWG とディジタル出力モジュールが動作を開始すると DAC と PMOD から下図の波形が観測できます．

| 色 | 信号 |
| --- | --- |
| 黄色 | AWG 0 |
| ピンク | PMOD 0 P0 |
| 緑 | PMOD 0 P1 |

![awg_pause_sync_0](images/awg_pause_0.jpg)

<br>

コンソールに `Press 'Enter' to resume AWGs` と表示されると AWG が一時停止され，波形の出力が止まります．
このとき，ディジタル出力モジュールも一時停止しており，出力値が一時停止前の値から変わらなくなります．
ここで，コンソール上で Enter を入力すると AWG およびディジタル出力モジュールは動作を再開し，下図の波形が観測できます．

![awg_pause_sync_1](images/awg_pause_1.jpg)

<br>

AWG とディジタル出力モジュールの動作再開から数秒で両方の動作が終了し，下図の波形が観測できます．

![awg_pause_sync_2](images/awg_pause_2.jpg)
