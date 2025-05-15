# AWG を外部トリガでスタートする

[awg_external_trigger.py](./awg_external_trigger.py) は AWG (Arbitrary Waveform Generator) を PMOD 1 のポート 0 に割り当てられた外部トリガからスタートするスクリプトです．

## セットアップ

DAC, PMOD とオシロスコープを接続します．

![セットアップ](./images/awg_x16_setup.png)


## 実行手順と結果

以下のコマンドを実行します．

```
python awg_external_trigger.py
```

コンソールに `Connect PMOD 0 port 0 to PMOD 1 port 1 and press 'Enter'` と表示されたら，下図の PMOD 0 の P0 と PMOD 1 の P0 を接続してから Enter を押します．

![PMOD](./images/pmod_ports.png)

ディジタル出力モジュール 0 からディジタル値が出力されると PMOD 0 のポート 0 の電圧が Lo から Hi に変わり，接続されている PMOD 1 の P0 を通して AWG のスタートトリガがかかります．

ディジタル出力モジュール と AWG が動作すると AWG と PMOD から下図の波形が観測できます．

| 色 | 信号 |
| --- | --- |
| 黄色 | AWG 0 |
| 水色 | AWG 1 |
| ピンク | PMOD 0 P0 |

![awg_external_trig_awg_0_1](./images/awg_external_trig_awg_0_1.jpg)

<br>

| 色 | 信号 |
| --- | --- |
| 黄色 | AWG 2 |
| 水色 | AWG 3 |
| ピンク | PMOD 0 P0 |

![awg_external_trig_awg_2_3](./images/awg_external_trig_awg_2_3.jpg)

<br>

| 色 | 信号 |
| --- | --- |
| 黄色 | AWG 4 |
| 水色 | AWG 5 |
| ピンク | PMOD 0 P0 |

![awg_external_trig_awg_4_5](./images/awg_external_trig_awg_4_5.jpg)

<br>

| 色 | 信号 |
| --- | --- |
| 黄色 | AWG 6 |
| 水色 | AWG 7 |
| ピンク | PMOD 0 P0 |

![awg_external_trig_awg_6_7](./images/awg_external_trig_awg_6_7.jpg)

<br>

| 色 | 信号 |
| --- | --- |
| 黄色 | AWG 8 |
| 水色 | AWG 9 |
| ピンク | PMOD 0 P0 |

![awg_external_trig_awg_8_9](./images/awg_external_trig_awg_8_9.jpg)

<br>

| 色 | 信号 |
| --- | --- |
| 黄色 | AWG 10 |
| 水色 | AWG 11 |
| ピンク | PMOD 0 P0 |

![awg_external_trig_awg_10_11](./images/awg_external_trig_awg_10_11.jpg)

<br>

| 色 | 信号 |
| --- | --- |
| 黄色 | AWG 12 |
| 水色 | AWG 13 |
| ピンク | PMOD 0 P0 |

![awg_external_trig_awg_8_9](./images/awg_external_trig_awg_12_13.jpg)

<br>

| 色 | 信号 |
| --- | --- |
| 黄色 | AWG 14 |
| 水色 | AWG 15 |
| ピンク | PMOD 0 P0 |

![awg_external_trig_awg_8_9](./images/awg_external_trig_awg_14_15.jpg)
