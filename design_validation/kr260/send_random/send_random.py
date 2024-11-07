"""
AWG から 50MHz の余弦波を出力して, 信号処理モジュールを全て無効にしてキャプチャします.
"""
import os
import argparse
import random
from e7awgsw import AWG, AwgCtrl, WaveSequence, E7AwgHwType

IP_ADDR = '10.0.0.16'
SAVE_DIR = "result_send_random/"

def gen_random_wave(wave_seq):
    samples = [random.randint(-32768, 32767)
            for _ in range(wave_seq.smallest_unit_of_wave_len)]
    return samples * random.randint(24, 40)


def gen_random_wave_seq(num_wait_words, awg_id):
    wave_seq = WaveSequence(
        num_wait_words = num_wait_words,
        num_repeats = random.randint(1, 2),
        design_type = E7AwgHwType.KR260)
    num_chunks = (awg_id % wave_seq.max_chunks) + 1

    for _ in range(num_chunks):
        i_samples = gen_random_wave(wave_seq)
        q_samples = [0] * len(i_samples)
        wave_seq.add_chunk(
            iq_samples = list(zip(i_samples, q_samples)),
            num_blank_words = random.randint(0, 4),
            num_repeats = random.randint(1, 3))
    return wave_seq


def set_wave_sequence(awg_ctrl, awgs, num_wait_words):
    awg_to_wave_sequence = {}
    for awg_id in awgs:
        wave_seq = gen_random_wave_seq(num_wait_words, awg_id)        
        awg_to_wave_sequence[awg_id] = wave_seq
        awg_ctrl.set_wave_sequence(awg_id, wave_seq)
    return awg_to_wave_sequence


def save_wave_data(prefix, id_to_samples, save_dir=SAVE_DIR):
    for id, samples in id_to_samples.items():
        dir = save_dir + '/{}_{}'.format(prefix, id)
        os.makedirs(dir, exist_ok = True)
        print('save {} {} data'.format(prefix, id))

        # I/Q データテキストファイル保存
        filepath = dir + '/wave_{}.txt'.format(id)
        with open(filepath, 'w') as txt_file:
            num = min(30000, len(samples))
            for i in range(num):
                txt_file.write("{}\n".format(samples[i]))
            if num < len(samples):
                txt_file.write("...\n")


def save_wave_signature(prefix, id_to_samples, save_dir=SAVE_DIR):
    for id, samples in id_to_samples.items():
        dir = save_dir + '/{}_{}'.format(prefix, id)
        os.makedirs(dir, exist_ok = True)
        print('save {} {} wave signature'.format(prefix, id))

        filepath = dir + '/signature_{}.txt'.format(id)
        sum_val = sum(samples) & 0xffffffff
        with open(filepath, 'w') as txt_file:
            txt_file.write("num words : {}\n".format(len(samples)))
            txt_file.write("sum : {:08x}\n".format(sum_val))


def check_err(awg_ctrl, awgs):
    awg_to_err = awg_ctrl.check_err(*awgs)
    for awg_id, err_list in awg_to_err.items():
        print(awg_id)
        for err in err_list:
            print('    {}'.format(err))


def main(
    awgs,
    num_wait_words,
    save_dir=SAVE_DIR,
    timeout=5):
    random.seed(10)
    with (AwgCtrl(IP_ADDR, E7AwgHwType.KR260) as awg_ctrl):
        # 初期化
        awg_ctrl.initialize(*awgs)
        # 波形シーケンスの設定
        awg_to_wave_sequence = set_wave_sequence(awg_ctrl, awgs, num_wait_words)
        # 波形送信スタート
        awg_ctrl.start_awgs(*awgs)
        # 波形送信完了待ち
        try:
            awg_ctrl.wait_for_awgs_to_stop(timeout, *awgs)
        except Exception as e:
            print(e)
            pass
        # エラーチェック
        check_err(awg_ctrl, awgs)
        # 波形保存
        awg_to_wave_data = {
            awg: list(map(lambda iq: iq[0], wave_seq.all_samples(False)))
            for awg, wave_seq in awg_to_wave_sequence.items()
        }
        save_wave_data('awg', awg_to_wave_data, save_dir)
        save_wave_signature('awg', awg_to_wave_data, save_dir)
        print('end')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--ipaddr')
    parser.add_argument('--awgs')
    parser.add_argument('--num-wait-words', default=0, type=int)
    parser.add_argument('--timeout', default=5, type=int)
    parser.add_argument('--save-dir', default=SAVE_DIR)
    args = parser.parse_args()

    if args.ipaddr is not None:
        IP_ADDR = args.ipaddr

    awgs = sorted(AWG.on(E7AwgHwType.KR260))
    if args.awgs is not None:
        awgs = [AWG.of(int(x)) for x in args.awgs.split(',')]

    main(
        awgs,
        args.num_wait_words,
        save_dir=args.save_dir,
        timeout=args.timeout)
