import e7awgsw as e7s
import e7awgsw.zcu111 as e7sz

digital_out_list = list(e7s.DigitalOut)

def set_digital_out_data(digital_out_ctrl):
    # ディジタル出力データの作成
    for dout_id in digital_out_list:
        dout_data_list = e7s.DigitalOutputDataList(e7s.E7AwgHwType.ZCU111)
        for i in range(10):
            bits = (dout_id << 8) + (i + 1)
            dout_data_list.add(bits, 2)
        # 出力データをディジタル出力モジュールに設定
        digital_out_ctrl.set_output_data(dout_data_list, dout_id)


def set_default_digital_out_data(digital_out_ctrl):
    # デフォルトのディジタル出力データの設定
    for dout_id in digital_out_list:
        bit_pattern = dout_id + 2
        digital_out_ctrl.set_default_output_data(bit_pattern, dout_id)


def setup_digital_output_modules(digital_out_ctrl):
    """ディジタル出力に必要な設定を行う"""
    # ディジタル出力モジュール初期化
    digital_out_ctrl.initialize(*digital_out_list)
    # デフォルトのディジタル出力データの設定
    set_default_digital_out_data(digital_out_ctrl)
    # ディジタル出力データの設定
    set_digital_out_data(digital_out_ctrl)


def main():
    zcu111_ip_addr = '192.168.1.3'
    fpga_ip_addr = '10.0.0.16'
    design_type = e7s.E7AwgHwType.ZCU111
    with (e7sz.RftoolTransceiver(zcu111_ip_addr, 15) as trasnceiver,
          e7s.DigitalOutCtrl(fpga_ip_addr, design_type) as digital_out_ctrl):
        # FPGA コンフィギュレーション
        e7sz.configure_fpga(trasnceiver, design_type)
        # ディジタル出力モジュールのセットアップ
        setup_digital_output_modules(digital_out_ctrl)
        # ディジタル出力スタート
        digital_out_ctrl.start_douts(*digital_out_list)
        # ディジタル出力モジュール動作完了待ち
        digital_out_ctrl.wait_for_douts_to_stop(5, *digital_out_list)
        # ディジタル出力モジュール動作完了フラグクリア
        digital_out_ctrl.clear_dout_stop_flags(*digital_out_list)


if __name__ == "__main__":
    main()
