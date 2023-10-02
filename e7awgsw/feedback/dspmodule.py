import numpy as np
from e7awgsw.feedback.hwdefs import DspUnit, DecisionFunc
from e7awgsw.captureparam import CaptureParam

def dsp(samples, capture_param):
    if len(samples) < capture_param.num_samples_to_process:
        samples.extend([(0, 0)] * (capture_param.num_samples_to_process - len(samples)))
    else:
        samples = samples[0:capture_param.num_samples_to_process]
    dsp_units_enabled = capture_param.dsp_units_enabled

    # 複素 FIR
    if DspUnit.COMPLEX_FIR in dsp_units_enabled:
        samples = complex_fir(samples, capture_param.complex_fir_coefs)

    # 間引き
    # 間引きが有効な場合, ここでポストブランクのデータは取り除かれる.
    if DspUnit.DECIMATION in dsp_units_enabled:
        samples_list = decimation(
            samples, 
            capture_param.sum_section_list, 
            capture_param.num_integ_sections,
            CaptureParam.NUM_REAL_FIR_COEFS)
    else:
        # 間引きが無効な場合, 後段の FIR がポストブランクのデータを使うので取り除かない.
        # Real FIR 用に先頭に 0 を付加する
        samples_list = [ [(0,0)] * 7 + samples ]

    # I と Q に分離
    i_samples_list = [] # [ [s00, s01, ... s0n], [s'10, s'11, ..s'1m] ... ]
    q_samples_list = []
    for samples in samples_list:
        i_samples_list.append([sample[0] for sample in samples])
        q_samples_list.append([sample[1] for sample in samples])

    # 実数 FIR
    if DspUnit.REAL_FIR in dsp_units_enabled:
        i_samples_list = real_fir(i_samples_list, capture_param.real_fir_i_coefs)
        q_samples_list = real_fir(q_samples_list, capture_param.real_fir_q_coefs)
    else:
        # Real FIR 用に付けた先頭のデータを取り除く
        start_idx = CaptureParam.NUM_REAL_FIR_COEFS - 1
        i_samples_list = [i_samples[start_idx:] for i_samples in i_samples_list]
        q_samples_list = [q_samples[start_idx:] for q_samples in q_samples_list]

    # 間引きが無効の場合, ここでポストブランクのサンプル削除
    if not DspUnit.DECIMATION in dsp_units_enabled:
        i_samples_list = remove_samples_in_post_blank(
            i_samples_list[0], capture_param.sum_section_list, capture_param.num_integ_sections)
        q_samples_list = remove_samples_in_post_blank(
            q_samples_list[0], capture_param.sum_section_list, capture_param.num_integ_sections)

    if DspUnit.COMPLEX_WINDOW in dsp_units_enabled:
        i_samples_list, q_samples_list = complex_window(
            i_samples_list, q_samples_list, capture_param.complex_window_coefs)

    if DspUnit.SUM in dsp_units_enabled:
        i_samples_list = summation(
            i_samples_list, capture_param.sum_start_word_no, capture_param.num_words_to_sum)
        q_samples_list = summation(
            q_samples_list, capture_param.sum_start_word_no, capture_param.num_words_to_sum)
    
    if DspUnit.INTEGRATION in dsp_units_enabled:
        i_samples_list = integration(
            i_samples_list, capture_param.num_sum_sections, capture_param.num_integ_sections)
        q_samples_list = integration(
            q_samples_list, capture_param.num_sum_sections, capture_param.num_integ_sections)

    num_frac_bits = 30 if DspUnit.COMPLEX_WINDOW in dsp_units_enabled else 0

    i_samples = sum(i_samples_list, [])
    q_samples = sum(q_samples_list, [])
    i_samples = [fixed_to_float(i_sample, num_frac_bits) for i_sample in i_samples]
    q_samples = [fixed_to_float(q_sample, num_frac_bits) for q_sample in q_samples]

    if DspUnit.CLASSIFICATION in dsp_units_enabled:
        results = classification(
            i_samples,
            q_samples,
            capture_param.get_decision_func_params(DecisionFunc.U0),
            capture_param.get_decision_func_params(DecisionFunc.U1))
        return results

    i_samples = [float(i_sample) for i_sample in i_samples]
    q_samples = [float(q_sample) for q_sample in q_samples]
    return list(zip(i_samples, q_samples))


def complex_fir(samples, coefs):
    num_taps = len(coefs)
    num_samples = len(samples)
    samples = ([(0, 0)] * (num_taps - 1)) + samples
    result = []
    for i in range(num_samples):    
        accumed = (0, 0)
        for j in range(len(coefs)):
            coef = coefs[num_taps - 1 - j]
            sample = samples[i + j]
            tmp = complex_mult_int(coef.real, coef.imag, sample[0], sample[1])
            accumed = complex_add_int(accumed[0], accumed[1], tmp[0], tmp[1])
        result.append(accumed)
    return result


def complex_mult_int(re_0, im_0, re_1, im_1):
    return (int(re_0) * int(re_1) - int(im_0) * int(im_1),
            int(re_0) * int(im_1) + int(im_0) * int(re_1))


def complex_add_int(re_0, im_0, re_1, im_1):
    return (int(re_0) + int(re_1), int(im_0) + int(im_1))


def remove_samples_in_post_blank(samples, sum_section_list, num_integ_sections):
    result = []
    idx = 0
    for _ in range(num_integ_sections):
        for sum_section in sum_section_list:
            sum_section_len = sum_section[0] * CaptureParam.NUM_SAMPLES_IN_ADC_WORD
            post_blank_len = sum_section[1] * CaptureParam.NUM_SAMPLES_IN_ADC_WORD
            result.append(samples[idx:idx + sum_section_len])
            idx += sum_section_len + post_blank_len
    return result


def decimation(samples, sum_section_list, num_integ_sections, num_fir_taps):
    """
    間引き処理は, 各総和区間内のサンプル数を 1/8 に減らす.
    間引き前のサンプル数を N, 間引き後のサンプル数を M とすると
    M = floor(N / 16) * 4  となる.
    リストのリストを返す.
    """
    result = []
    idx = 0
    for _ in range(num_integ_sections):
        for sum_section in sum_section_list:
            sum_section_len = sum_section[0] * CaptureParam.NUM_SAMPLES_IN_ADC_WORD
            post_blank_len = sum_section[1] * CaptureParam.NUM_SAMPLES_IN_ADC_WORD
            num_samples_left = sum_section_len // 16 * CaptureParam.NUM_SAMPLES_IN_ADC_WORD
            samples_left = samples[idx:idx + sum_section_len:4][0:num_samples_left]
            
            # 後段の FIR 用のデータを付加する
            proceding = [(0, 0) if j < 0 else samples[j] for j in range(idx - (num_fir_taps - 1) * 4, idx, 4)]
            result.append(proceding + samples_left)
            idx += sum_section_len + post_blank_len
    return result


def real_fir(samples_list, coefs):
    num_taps = len(coefs)
    result = []
    for samples in samples_list:
        num_samples = len(samples) - (num_taps - 1)
        filtered = []
        for i in range(num_samples):
            accumed = 0
            for j in range(len(coefs)):
                accumed += samples[i + j] * coefs[num_taps - 1 - j]
            filtered.append(accumed)
        result.append(filtered)
    return result


def complex_window(i_samples_list, q_samples_list, coefs):
    i_result = []
    q_result = []
    num_taps = len(coefs)
    for i in range(len(i_samples_list)):
        i_samples = i_samples_list[i]
        q_samples = q_samples_list[i]
        num_samples = len(i_samples)
        i_applied = []
        q_applied = []
        for j in range(num_samples):
            coef = coefs[j % num_taps]
            tmp = complex_mult_int(i_samples[j], q_samples[j], coef.real, coef.imag)
            i_applied.append(tmp[0])
            q_applied.append(tmp[1])
        i_result.append(i_applied)
        q_result.append(q_applied)
    return (i_result, q_result)


def summation(samples_list, sum_start_word_no, num_words_to_sum):
    result = []
    for samples in samples_list:
        num_samples = len(samples)
        sum_start_sample_idx = sum_start_word_no * CaptureParam.NUM_SAMPLES_IN_ADC_WORD
        sum_start_sample_idx = max(sum_start_sample_idx, 0)
        sum_end_sample_idx = (sum_start_word_no + num_words_to_sum) * CaptureParam.NUM_SAMPLES_IN_ADC_WORD - 1
        sum_end_sample_idx = min(sum_end_sample_idx, num_samples - 1)
        samples_to_sum = samples[sum_start_sample_idx:sum_end_sample_idx + 1]
        if len(samples_to_sum) >= 1:
            result.append([sum(samples_to_sum)])
        else:
            result.append([])
    return result


def integration(sample_list, num_sum_sections, num_integ_sections):
    result = []
    for i in range(num_sum_sections):
        integ_list = [0] * len(sample_list[i])
        for j in range(num_integ_sections):
            samples = sample_list[j * num_sum_sections + i]
            for k in range(len(integ_list)):
                integ_list[k] += samples[k]
        result.append(integ_list)
    return result


def classification(
    i_sample_list, q_sample_list, decision_func_params_0, decision_func_params_1):
    result = []
    a0, b0, c0 = decision_func_params_0
    a1, b1, c1 = decision_func_params_1
    for i in range(len(i_sample_list)):
        i_val = i_sample_list[i]
        q_val = q_sample_list[i]
        res_0 = a0 * i_val + b0 * q_val + c0
        res_1 = a1 * i_val + b1 * q_val + c1
        if (res_0 >= 0) and (res_1 >= 0):
            result.append(0)
        elif (res_0 >= 0) and (res_1 < 0):
            result.append(1)
        elif (res_0 < 0) and (res_1 >= 0):
            result.append(2)
        elif (res_0 < 0) and (res_1 < 0):
            result.append(3)
    return result


def float_to_raw_bits(val):
    return int.from_bytes(val.tobytes(), 'little')


def rawbits_to_float(val):
    return np.frombuffer(val.to_bytes(4, 'little'), dtype='float32')[0]


def fixed_to_float(val, num_frac_bits):
    negative = False
    val = val & 0x1_FFFFFFFFFF_FFFFFFFFFF_FFFFFFFFFF
    if val & 0x1_0000000000_0000000000_0000000000:
        negative = True
        val = -val

    dval0 = np.float32(val & 0xFFFFFFFF_FFFFFFFF)
    dval1 = np.float32((val >> 64) & 0x1_FFFF_FFFFFFFFFF)
    raw_val0 = float_to_raw_bits(dval0)
    raw_val1 = float_to_raw_bits(dval1)
    exp0 = ((raw_val0 >> 23) +  0 - num_frac_bits) & 0xFF if dval0 != 0.0 else 0
    exp1 = ((raw_val1 >> 23) + 64 - num_frac_bits) & 0xFF if dval1 != 0.0 else 0
    raw_val0 = (raw_val0 & 0x80000000) | (exp0 << 23) | (raw_val0 & 0x7FFFFF)
    raw_val1 = (raw_val1 & 0x80000000) | (exp1 << 23) | (raw_val1 & 0x7FFFFF)
    raw_val0 &= 0xFFFFFFFF
    raw_val1 &= 0xFFFFFFFF
    dval0 = rawbits_to_float(raw_val0)
    dval1 = rawbits_to_float(raw_val1)
    if negative:
        return -(dval0 + dval1)
    return dval0 + dval1
