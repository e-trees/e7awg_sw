import time
import e7awgsw as e7s
import e7awgsw.zcu111 as e7sz

awg_list = [e7s.AWG.U0, e7s.AWG.U1]
wave_freq = 1 # MHz
mixer_freq = 0 # MHz

def get_dac_interrupts(rfdc_ctrl):
    """全ての DAC の割り込みを取得する"""
    dac_to_interrupts = {}
    for tile in list(e7sz.DacTile):
        dac_to_interrupts[tile] = {}
        for channel in list(e7sz.DacChannel):
            dac_to_interrupts[tile][channel] = rfdc_ctrl.get_dac_interrupts(tile, channel)
    
    return dac_to_interrupts


def output_rfdc_interrupt_details(dac_to_interrupts):
    """RF Data Converter の割り込みを出力する"""
    for tile, channel_to_interrupts in dac_to_interrupts.items():
        for channel, interrupts in channel_to_interrupts.items():
            if len(interrupts) != 0:
                print('Interrupts on DAC tile {}, channel {}'.format(tile, channel))
            for interrupt in interrupts:
                print('  ', e7sz.RfdcInterrupt.to_msg(interrupt))


def output_awg_err_details(awg_to_errs):
    """AWG のエラーを出力する"""
    for awg, errs in awg_to_errs.items():
        print('Errors on AWG {}'.format(awg))
        for err in errs:
            print('  ', e7s.AwgErr.to_msg(err))
        print()


def gen_wave_samples(freq, num_cycles, sampling_rate, hw_specs):
    """出力波形を構成するサンプルデータを作成する"""
    wave = e7s.SinWave(num_cycles, freq, 25000)
    # DAC の I/Q ミキサが有効な場合, RF Data Converter 内部で波形データが補間されるので, あらかじめ 1/2 に間引いておく.
    samples = wave.gen_samples(sampling_rate)[0::2]
    return e7s.IqWave.convert_to_iq_format(
        samples, samples, hw_specs.awg.smallest_unit_of_wave_len)


def set_waves(awg_ctrl, sampling_rate, hw_specs):
    awg_to_wave_seq = {}
    for awg_id in awg_list:
        wave_seq = e7s.WaveSequence(0, 1, e7s.E7AwgHwType.ZCU111)
        samples = gen_wave_samples(wave_freq * 1e6, 3, sampling_rate, hw_specs)
        wave_seq.add_chunk(samples, 0, 1)
        awg_ctrl.set_wave_sequence(awg_id, wave_seq)
        awg_to_wave_seq[awg_id] = wave_seq

    return awg_to_wave_seq


def setup_awgs(awg_ctrl, sampling_rate, hw_specs):
    """AWG の波形出力に必要な設定を行う"""
    # AWG 初期化
    awg_ctrl.initialize(*awg_list)
    # 波形データを AWG に設定
    return set_waves(awg_ctrl, sampling_rate, hw_specs)


def set_digital_out_data(digital_out_ctrl, bit_patterns):
    # ディジタル出力データの作成
    dout_data_list = e7s.DigitalOutputDataList(e7s.E7AwgHwType.ZCU111)
    for bit_pattern in bit_patterns:
        dout_data_list.add(bit_pattern, 276480000) # 4 [sec]

    # 出力データをディジタル出力モジュールに設定
    digital_out_ctrl.set_output_data(dout_data_list, e7s.DigitalOut.U0)


def setup_digital_output_modules(digital_out_ctrl):
    """ディジタル出力に必要な設定を行う"""
    # ディジタル出力モジュール初期化
    digital_out_ctrl.initialize(e7s.DigitalOut.U0)
    # デフォルトのディジタル出力データの設定
    digital_out_ctrl.set_default_output_data(0, e7s.DigitalOut.U0)
    # ディジタル出力データの設定
    bit_patterns = [1, 2]
    set_digital_out_data(digital_out_ctrl, bit_patterns)
    # AWG からのリスタートトリガを受け付けるように設定.
    # このリスタートトリガは, いずれかの AWG の波形出力開始と同時にアサートされる.
    digital_out_ctrl.enable_trigger(e7s.DigitalOutTrigger.RESTART, e7s.DigitalOut.U0)



def setup_dacs(rfdc_ctrl):
    """DAC の設定を行う"""
    for tile in list(e7sz.DacTile):
        # FIFO 無効化
        rfdc_ctrl.disable_dac_fifo(tile)
        for channel in list(e7sz.DacChannel):
            # ミキサを設定
            rfdc_ctrl.set_dac_mixer_settings(tile, channel, mixer_freq, 0, e7sz.MixerScale.V0P7)
            # DAC 割り込みクリア
            rfdc_ctrl.clear_dac_interrupts(tile, channel, *list(e7sz.RfdcInterrupt))
            # DAC 割り込み有効化
            rfdc_ctrl.enable_dac_interrupts(tile, channel, *list(e7sz.RfdcInterrupt))
        # FIFO 有効化
        rfdc_ctrl.enable_dac_fifo(tile)
    
    # DAC タイルを同期させる.  ミキサの設定を行ってから実行する必要がある.
    rfdc_ctrl.sync_dac_tiles()


def restart_douts(mode, awg_ctrl, digital_out_ctrl):
    """ディジタル出力モジュールを再スタートする"""
    if mode == 1:
        # 再スタート
        digital_out_ctrl.restart_douts(e7s.DigitalOut.U0)
    else:
        # AWG の波形出力スタート.
        # AWG の波形出力開始に合わせてディジタル出力モジュールが再スタートする.
        awg_ctrl.start_awgs(*awg_list)
        # 波形出力完了待ち
        awg_ctrl.wait_for_awgs_to_stop(5, *awg_list)


def main():
    zcu111_ip_addr = '192.168.1.3'
    fpga_ip_addr = '10.0.0.16'
    hw_specs = e7s.E7AwgHwSpecs(e7s.E7AwgHwType.ZCU111)
    with (e7sz.RftoolTransceiver(zcu111_ip_addr, 15) as trasnceiver,
          e7sz.RfdcCtrl(trasnceiver, e7s.E7AwgHwType.ZCU111) as rfdc_ctrl,
          e7s.AwgCtrl(fpga_ip_addr, e7s.E7AwgHwType.ZCU111) as awg_ctrl,
          e7s.DigitalOutCtrl(fpga_ip_addr, e7s.E7AwgHwType.ZCU111) as digital_out_ctrl):
        # FPGA コンフィギュレーション
        print('configure fpga')
        e7sz.configure_fpga(trasnceiver, e7s.E7AwgHwType.ZCU111)
        # DAC のセットアップ
        print('setup DACs')
        setup_dacs(rfdc_ctrl)
        # AWG のセットアップ
        print('setup AWGs')
        sampling_rate = rfdc_ctrl.get_dac_sampling_rate(e7sz.DacTile.T0) * 1e6 # Hz
        setup_awgs(awg_ctrl, sampling_rate, hw_specs)
        # ディジタル出力モジュールのセットアップ
        print('setup digital output modules')
        setup_digital_output_modules(digital_out_ctrl)
        # ディジタル出力スタート
        print('start a digital output modules')
        digital_out_ctrl.start_douts(e7s.DigitalOut.U0)
        time.sleep(2)
        # ディジタル出力一時停止
        digital_out_ctrl.pause_douts(e7s.DigitalOut.U0)
        ctrl_sel = input('\ninput\n    0: resume\n    1: restart from software\n    2: restart from AWG\n')

        if int(ctrl_sel) == 0:
            # 再開
            digital_out_ctrl.resume_douts(e7s.DigitalOut.U0)
        else:
            # ディジタル出力データを変更
            bit_patterns = [3, 2, 1]
            set_digital_out_data(digital_out_ctrl, bit_patterns)
            # 再スタート
            restart_douts(int(ctrl_sel), awg_ctrl, digital_out_ctrl)

        # ディジタル出力モジュール動作完了待ち
        print('wait for a digital output module to stop')
        digital_out_ctrl.wait_for_douts_to_stop(15, e7s.DigitalOut.U0)
        # 波形出力完了フラグクリア
        awg_ctrl.clear_awg_stop_flags(*awg_list)
        # ディジタル出力モジュール動作完了フラグクリア
        digital_out_ctrl.clear_dout_stop_flags(e7s.DigitalOut.U0)
        # DAC 割り込みチェック
        dac_to_interrupts = get_dac_interrupts(rfdc_ctrl)
        output_rfdc_interrupt_details(dac_to_interrupts)
        # AWG エラーチェック
        awg_to_errs = awg_ctrl.check_err(*awg_list)
        output_awg_err_details(awg_to_errs)


if __name__ == "__main__":
    main()
