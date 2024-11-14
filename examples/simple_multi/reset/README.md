# AWG とキャプチャモジュールをリセットする

[reset.py](./reset.py) は AWG およびキャプチャモジュールをリセットもしくは初期化するスクリプトです．

## 実行方法

以下のコマンドを実行します．

**send_recv.py**  
```
python reset.py [オプションリスト]
```

|  オプション  |  説明 | 設定例 |
| ---- | ---- | ---- |
| --init | AWG およびキャプチャモジュールを初期化する．<br> 初期化にはリセットも含まれる．<br> デフォルト値: リセットのみ実行する| --init |
|--ipaddr| AWG コントローラとキャプチャコントローラの IP アドレス <br> デフォルト値: 10.0.0.16 | --ipadd=10.0.0.5 |
|--awgs| 使用する AWG <br> デフォルト値: 全 AWG | --awgs=0,7,12 |
|--capture-module| 使用するキャプチャモジュール <br> デフォルト値: 全キャプチャモジュール | --capture-module=0 |
|--labrad| LabRAD サーバ経由で HW を制御する <br> デフォルト値: LabRAD を使用しない| --labrad |
|--server-ipaddr| LabRAD サーバの IP アドレス <br> デフォルト値: localhost | --server-ipaddr=192.168.0.6 |

## 実行結果

コンソールに`end`と表示されればリセットもしくは初期化完了です．
