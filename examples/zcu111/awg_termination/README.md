# AWG を強制停止する

[awg_termination.py](./awg_termination.py) は波形を出力中の AWG を強制停止するスクリプトです．
本スクリプトは ZCU111 版 e7awg_hw の `デザイン 0 ~ 2` に対応しています．
各デザインのモジュール構成については，[e7awg_hw ユーザマニュアル](../../../manuals/zcu111/hw/README.md) を参照してください．

本スクリプトで動作する AWG と上述のデザインの対応関係は以下の表の通りです．

| デザイン ID | AWG |
| --- | --- |
| 0 | 0, 1 |
| 1 | 0 |
| 2 | 0, 1 |

## セットアップ

DAC, PMOD とオシロスコープを接続します．

![セットアップ](./images/awg_x2_setup.png)

<br>

![PMOD](./images/pmod_ports.png)

## 実行手順と結果

以下のコマンドを実行します．

```
# デザイン 0 を使用する場合
python awg_termination.py

# デザイン 1 を使用する場合
python awg_termination.py  --design-type=dac6g

# デザイン 2 を使用する場合
python awg_termination.py  --design-type=dac1g-uram2
```

DAC から下図のような波形が連続的に出力されます．
PMOD は 全てのポートが Hi になります．
「press Enter to stop AWGs.」と表示されたら Enter を押してください．
DAC の波形出力と PMOD からのディジタル値の出力が止まります．

| 色 | 信号 | 
| --- | --- | 
| 黄色 | AWG 0 |
| 水色 | AWG 1 |
| ピンク | PMOD 0 P0 |

![AWG 0, AWG 1, PMOD 0 の波形](images/awg_0_1_pmod_0.jpg)
