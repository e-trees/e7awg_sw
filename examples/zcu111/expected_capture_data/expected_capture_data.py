import e7awgsw.basiccapture as bc


def calc_real_expected_data(
    cap_param: bc.CaptureParam, cap_data: list[int], num_samples_in_cap_word: int) -> None:
    """cap_data に cap_param を適用してキャプチャした場合の期待値を算出する.

    | cap_data には, キャプチャターゲットのサンプルだけを集めたリストを渡すこと.

    """
    start_of_cap_step = 0
    expected = []
    num_sum_samples = cap_param.num_sum_words * num_samples_in_cap_word
    for cap_step in cap_param.capture_steps:
        num_samples_in_cap_target = cap_step[0] * num_samples_in_cap_word
        target_samples = cap_data[start_of_cap_step : start_of_cap_step + num_samples_in_cap_target]
        if bc.DspUnit.SUM in cap_param.dsp_list:
            target_samples = _sum(target_samples, num_sum_samples)

        if bc.DspUnit.BINARIZATION in cap_param.dsp_list:
            target_samples = _binarization(target_samples, cap_param.real_bin_threshold)

        if bc.DspUnit.REDUCTION in cap_param.dsp_list:
            target_samples = _reduction(target_samples, cap_param.real_reduction_op)
        
        expected.extend(target_samples)
        start_of_cap_step += num_samples_in_cap_target

    return expected


def _sum(samples: list[int], num_sum_samples: int):
    expected = []
    num_sums = len(samples) // num_sum_samples
    for i in range(num_sums):
        expected.append(sum(samples[i * num_sum_samples : (i + 1) * num_sum_samples]))
    
    return expected


def _binarization(samples: list[int], threshold: int):
    expected = []
    for sample in samples:
        result = 1 if sample >= threshold else 0
        expected.append(result)

    return expected


def _reduction(samples: list[int], op: bc.ReductionOperation):
    # reduction は 1 以上のサンプルの個数によって結果が変わる
    binarized = _binarization(samples, 1)

    if op == bc.ReductionOperation.ALL:
        # samples が空なら [1] を返すが, それで正しい
        return [0] if 0 in binarized else [1]

    if op == bc.ReductionOperation.ANY:
        return [1] if 1 in binarized else [0]

    raise ValueError(f"Unknown Reduction Operation ({op})")
