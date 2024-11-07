# AWG から波形を出力し続ける

[long_send.py](./long_send.py) は AWG から波形を出力し続けるスクリプトです．

## 実行方法

以下のコマンドを実行します．

```
python long_send.py [オプションリスト]
```

|  オプション  |  説明 | 設定例 |
| ---- | ---- | ---- |
|--ipaddr| AWG コントローラとキャプチャコントローラの IP アドレス <br> デフォルト値: 10.0.0.16 | --ipadd=10.0.0.5 |
|--awgs| 使用する AWG <br> デフォルト値: 全 AWG | --awgs=0,7,12 |
|--labrad| LabRAD サーバ経由で HW を制御する <br> デフォルト値: LabRAD を使用しない| --labrad |
|--server-ipaddr| LabRAD サーバの IP アドレス <br> デフォルト値: localhost | --server-ipaddr=192.168.0.6 |

## 実行結果

コンソールに`end`と出力されればプログラム終了です．プログラムが終了した後も AWG は波形を出力し続けている点に注意してください．


# AWG の波形出力を止める
[stop_awgs.py](./stop_awgs.py) は AWG の波形出力を強制的に停止させるスクリプトです．

## 実行方法

以下のコマンドを実行します．

```
python stop_awgs.py [オプションリスト]
```

|  オプション  |  説明 | 設定例 |
| ---- | ---- | ---- |
|--ipaddr| AWG コントローラとキャプチャコントローラの IP アドレス <br> デフォルト値: 10.0.0.16 | --ipadd=10.0.0.5 |
|--awgs| 使用する AWG <br> デフォルト値: 全 AWG | --awgs=0,7,12 |
|--labrad| LabRAD サーバ経由で HW を制御する <br> デフォルト値: LabRAD を使用しない| --labrad |
|--server-ipaddr| LabRAD サーバの IP アドレス <br> デフォルト値: localhost | --server-ipaddr=192.168.0.6 |

## 実行結果

コンソールに`end`と出力されればプログラム終了です．
