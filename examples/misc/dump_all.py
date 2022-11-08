import sys
import pathlib
import argparse
import numpy as np
from collections import OrderedDict
from typing import Any, Sequence, List, Tuple, Set, Dict, Optional, Callable, cast

lib_path = str(pathlib.Path(__file__).resolve().parents[2])
sys.path.append(lib_path)
from e7awgsw import AWG, CaptureUnit
from e7awgsw.udpaccess import RegAccess, AwgRegAccess, CaptureRegAccess
from e7awgsw.hwparam import AWG_REG_PORT, CAPTURE_REG_PORT
from e7awgsw.memorymap import AwgMasterCtrlRegs, AwgCtrlRegs, WaveParamRegs, \
    CaptureMasterCtrlRegs, CaptureCtrlRegs, CaptureParamRegs

DEFAULT_IPADDR = '10.0.0.16'

# XXX: should be provided by AwgCtrlRegs or something.
NUM_CHUNKS = 16

# XXX: should be provided by CaptureParamRegs.
CAP_PARAM_NUM_SUM_SECTIONS = 4096
CAP_PARAM_NUM_POST_BLANKS = 4096
CAP_PARAM_NUM_COMP_FIR_REAL_COEFS = 16
CAP_PARAM_NUM_COMP_FIR_IMAG_COEFS = 16
CAP_PARAM_NUM_REAL_FIR_I_DATA_COEFS = 8
CAP_PARAM_NUM_REAL_FIR_Q_DATA_COEFS = 8
CAP_PARAM_NUM_COMP_WINDOW_REAL_COEFS = 2048
CAP_PARAM_NUM_COMP_WINDOW_IMAG_COEFS = 2048
CAP_PARAM_NUM_DECISION_FUNC_PARAMS = 6


def _convert_to_reg_list(reg_map: Any, cond: Optional[Set[str]] = None) -> List[Tuple[int, str]]:
    return sorted([(v, k) for k, v in reg_map.Offset.__dict__.items()
                   if k[0] != '_' and isinstance(v, int) and (cond is None or k in cond)])


def _dump_register_file(reg_access: RegAccess, base_addr: int, reg_list: List[Tuple[int, str]]) -> OrderedDict:
    reg_value = OrderedDict()
    for offset, name in reg_list:
        reg_value[name] = reg_access.read(base_addr, offset)
    return reg_value


def _dump_cap_parameters(cap_reg_access: CaptureRegAccess, cap_id: CaptureUnit,
                         address_calc: Callable[[int], int], start: int, end: int, signed: bool) -> np.array:
    elem_size = address_calc(1) - address_calc(0)
    # NOTES: some register has 16-bit value, however the 32-bit whole word is kept for the debug purpose.
    if elem_size == 4:
        dtype = np.int32 if signed else np.uint32
    else:
        raise RuntimeError(f"unsupported element size: {elem_size:d}")

    # XXX: intentionally avoid to use multi_read() before clarifying the conditions that it works well.
    # TODO: confirm the condition and revise the code accordingly.
    vec = np.zeros(end - start, dtype=dtype)
    for i in range(start, end):
        # be aware that read() return signed int.
        v = cap_reg_access.read(CaptureParamRegs.Addr.capture(cap_id), address_calc(i))
        if not signed:
            v = v if v >= 0 else v + (1 << (elem_size * 8 - 1))
        vec[i] = v
    return vec


def dump_awg_ctrl_master(awg_reg_access: AwgRegAccess) -> OrderedDict:
    # Do I need to set CTRL_TARGET_SEL to 0xf before reading?
    # --> No. this tools should not modify the contents of any registers.
    return _dump_register_file(
        cast(RegAccess, awg_reg_access),
        AwgMasterCtrlRegs.ADDR,
        _convert_to_reg_list(AwgMasterCtrlRegs)
    )


def dump_awg_ctrl(awg_reg_access: AwgRegAccess, awg_id: AWG) -> OrderedDict:
    return _dump_register_file(
        cast(RegAccess, awg_reg_access),
        AwgCtrlRegs.Addr.awg(awg_id),
        _convert_to_reg_list(AwgCtrlRegs)
    )


def dump_wave_param_whole(awg_reg_access: AwgRegAccess, awg_id: AWG) -> OrderedDict:
    return _dump_register_file(
        cast(RegAccess, awg_reg_access),
        WaveParamRegs.Addr.awg(awg_id),
        _convert_to_reg_list(WaveParamRegs,
                             {"NUM_WAIT_WORDS", "NUM_REPEATS", "NUM_CHUNKS", "WAVE_STARTABLE_BLOCK_INTERVAL"})
    )


def dump_wave_param_chunk(awg_reg_access: AwgRegAccess, awg_id: AWG, chunk_id: int) -> OrderedDict:
    return _dump_register_file(
        cast(RegAccess, awg_reg_access),
        WaveParamRegs.Addr.awg(awg_id) + WaveParamRegs.Offset.chunk(chunk_id),
        _convert_to_reg_list(WaveParamRegs,
                             {"CHUNK_START_ADDR", "NUM_WAVE_PART_WORDS", "NUM_BLANK_WORDS", "NUM_CHUNK_REPEATS"})
    )


def dump_wave_param(awg_reg_access: AwgRegAccess, awg_id: AWG) -> OrderedDict:
    value = dump_wave_param_whole(awg_reg_access, awg_id)
    for chunk_id in range(NUM_CHUNKS):
        value[f"CHUNK_{chunk_id:02d}"] = dump_wave_param_chunk(awg_reg_access, awg_id, chunk_id)
    return value


def dump_awg_all(awg_reg_access: AwgRegAccess,
                 awg_ids: Optional[Sequence[AWG]] = None) -> Tuple[OrderedDict, OrderedDict]:
    ctrl = dump_awg_ctrl_master(awg_reg_access)
    wave = OrderedDict()
    if awg_ids is None:
        awg_ids = AWG.all()
    for awg_id in awg_ids:
        ctrl[f"AWG_{awg_id:02d}"] = dump_awg_ctrl(awg_reg_access, awg_id)
        wave[f"AWG_{awg_id:02d}"] = dump_wave_param(awg_reg_access, awg_id)
    return ctrl, wave


def dump_cap_ctrl_master(cap_reg_access: CaptureRegAccess):
    return _dump_register_file(
        cast(RegAccess, cap_reg_access),
        CaptureMasterCtrlRegs.ADDR,
        _convert_to_reg_list(CaptureMasterCtrlRegs)
    )


def dump_cap_ctrl(cap_reg_access: CaptureRegAccess, cap_id: CaptureUnit) -> OrderedDict:
    return _dump_register_file(
        cast(RegAccess, cap_reg_access),
        CaptureCtrlRegs.Addr.capture(cap_id),
        _convert_to_reg_list(CaptureCtrlRegs)
    )


def dump_cap_param_flag(cap_reg_access: CaptureRegAccess, cap_id: CaptureUnit) -> OrderedDict:
    return _dump_register_file(
        cast(RegAccess, cap_reg_access),
        CaptureParamRegs.Addr.capture(cap_id),
        _convert_to_reg_list(CaptureParamRegs)
    )


def dump_cap_param_vector(cap_reg_access: CaptureRegAccess, cap_id: CaptureUnit) -> Dict[str, np.array]:
    v = OrderedDict()
    v['sum_section'] = _dump_cap_parameters(cap_reg_access, cap_id,
                                            CaptureParamRegs.Offset.sum_section_length,
                                            0, CAP_PARAM_NUM_SUM_SECTIONS,
                                            False)
    v['post_blank'] = _dump_cap_parameters(cap_reg_access, cap_id,
                                           CaptureParamRegs.Offset.post_blank_length,
                                           0, CAP_PARAM_NUM_POST_BLANKS,
                                           False)
    v['comp_fir_re_coef'] = _dump_cap_parameters(cap_reg_access, cap_id,
                                                 CaptureParamRegs.Offset.comp_fir_re_coef,
                                                 0, CAP_PARAM_NUM_COMP_FIR_REAL_COEFS,
                                                 True)
    v['comp_fir_im_coef'] = _dump_cap_parameters(cap_reg_access, cap_id,
                                                 CaptureParamRegs.Offset.comp_fir_im_coef,
                                                 0, CAP_PARAM_NUM_COMP_FIR_IMAG_COEFS,
                                                 True)
    v['real_fir_i_coef'] = _dump_cap_parameters(cap_reg_access, cap_id,
                                                CaptureParamRegs.Offset.real_fir_i_coef,
                                                0, CAP_PARAM_NUM_REAL_FIR_I_DATA_COEFS,
                                                True)
    v['real_fir_q_coef'] = _dump_cap_parameters(cap_reg_access, cap_id,
                                                CaptureParamRegs.Offset.real_fir_q_coef,
                                                0, CAP_PARAM_NUM_REAL_FIR_Q_DATA_COEFS,
                                                True)
    v['comp_window_re_coef'] = _dump_cap_parameters(cap_reg_access, cap_id,
                                                    CaptureParamRegs.Offset.comp_window_re_coef,
                                                    0, CAP_PARAM_NUM_COMP_WINDOW_REAL_COEFS,
                                                    True)
    v['comp_window_im_coef'] = _dump_cap_parameters(cap_reg_access, cap_id,
                                                    CaptureParamRegs.Offset.comp_window_im_coef,
                                                    0, CAP_PARAM_NUM_COMP_WINDOW_IMAG_COEFS,
                                                    True)
    v['decision_func_param'] = _dump_cap_parameters(cap_reg_access, cap_id,
                                                    CaptureParamRegs.Offset.decision_func_params,
                                                    0, CAP_PARAM_NUM_DECISION_FUNC_PARAMS,
                                                    True)
    return v


def dump_cap_all(cap_reg_access: CaptureRegAccess,
                 cap_ids: Optional[Sequence[CaptureUnit]] = None,
                 enable_vector: bool = True) -> Tuple[OrderedDict, OrderedDict, OrderedDict]:
    ctrl = dump_cap_ctrl_master(cap_reg_access)
    param = OrderedDict()
    vector = OrderedDict()
    if cap_ids is None:
        cap_ids = CaptureUnit.all()
    for cap_id in cap_ids:
        label = f"CAP_{cap_id:02d}"
        ctrl[label] = dump_cap_ctrl(cap_reg_access, cap_id)
        param[label] = dump_cap_param_flag(cap_reg_access, cap_id)
        if enable_vector:
            vector[label] = dump_cap_param_vector(cap_reg_access, cap_id)
    return ctrl, param, vector


def show_registers(reg_values: OrderedDict, indent_unit: int = 4, indent_level: int = 0) -> None:
    indent = indent_unit * indent_level
    for k, v in reg_values.items():
        if isinstance(v, int):
            print(f"{' ' * indent:s}{k:<20s}:\t{v:08x}")
        elif isinstance(v, OrderedDict):
            print(f"{' ' * indent:s}{k + ':':<20s}")
            show_registers(v, indent_unit, indent_level + 1)


def show_vectors(vector_dict: OrderedDict, indent: int = 4) -> None:
    for cap_id, vectors in vector_dict.items():
        print(f"{cap_id:s}:")
        for name, vector in vectors.items():
            for i in range(len(vector)):
                print(f"{' ' * indent:s}{name:s}[{i:04d}] = {vector[i]:6d}")
            print()
        print()


def show_vectors_complex(vector_dict: OrderedDict, indent: int = 4) -> None:
    for cap_id, vectors in vector_dict.items():
        print(f"{cap_id:s}:")
        for names in [("sum_section", "post_blank"),
                      ("comp_fir_re_coef", "comp_fir_im_coef"),
                      ("real_fir_i_coef", "real_fir_q_coef"),
                      ("comp_window_re_coef", "comp_window_im_coef")]:
            v0 = vectors[names[0]]
            v1 = vectors[names[1]]
            assert (len(v0) == len(v1))
            for i in range(len(v0)):
                print(f"{' ' * indent:s}({names[0]:s}, {names[1]:s})[{i:04d}] = ({v0[i]:6d}, {v1[i]:6d})")
            print()
        for name in ["decision_func_param"]:
            vector = vectors[name]
            for i in range(len(vector)):
                print(f"{' ' * indent:s}{name:s}[{i:04d}] = {vector[i]:6d}")
            print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="a universal register dump script for e7awg_hw")
    parser.add_argument('--ipaddr', type=str, default=DEFAULT_IPADDR,
                        help="IP address of the target box")
    parser.add_argument('--awgs', type=str, default="",
                        help="a comma separated list of AWG channels to be dumped." 
                             " All channels are dumped by default.")
    parser.add_argument('--caps', type=str, default="",
                        help="a comman separated list of CaptureUnit channels to be dumped."
                             " All channels are dumped by default.")
    parser.add_argument('--awg_ctrl', action='store_true',
                        help="activating the dump of AWG control registers")
    parser.add_argument('--awg_wave', action='store_true',
                        help="activating the dump of AWG wave registers")
    parser.add_argument('--cap_ctrl', action='store_true',
                        help="activating the dump of CaptureUnit control registers")
    parser.add_argument('--cap_param', action='store_true',
                        help="activating the dump of CaptureUnit parameter registers")
    parser.add_argument('--cap_param_vector', action='store_true',
                        help="activating the dump of all the vector data of CaptureUnit parameter registers."
                             " this dump is never generated without your explicit activation because it is very long")
    args = parser.parse_args()

    target_awgs = []
    target_caps = []
    if args.awgs == "" and args.caps == "":
        target_awgs = AWG.all()
        target_caps = CaptureUnit.all()
    else:
        # noinspection PyBroadException
        try:
            if args.awgs != "":
                all_awgs = AWG.all()
                target_awgs = [all_awgs[int(i)] for i in args.awgs.split(',')]
            if args.caps != "":
                all_caps = CaptureUnit.all()
                target_caps = [all_caps[int(i)] for i in args.caps.split(',')]
        except Exception:
            parser.print_help()
            sys.exit(0)

    # NOTE: enable_cap_param_vector is enabled only when it is explicitly enabled by the argument.
    enable_awg_ctrl = args.awg_ctrl
    enable_awg_wave = args.awg_wave
    enable_cap_ctrl = args.cap_ctrl
    enable_cap_param = args.cap_param
    enable_cap_param_vector = args.cap_param_vector
    if not (enable_awg_ctrl or enable_awg_wave or enable_cap_ctrl or enable_cap_param):
        enable_awg_ctrl = True
        enable_awg_wave = True
        enable_cap_ctrl = True
        enable_cap_param = True

    awg_reg_access_i = AwgRegAccess(args.ipaddr, AWG_REG_PORT)
    cap_reg_access_i = CaptureRegAccess(args.ipaddr, CAPTURE_REG_PORT)

    if len(target_awgs) > 0 and (enable_awg_ctrl or enable_awg_wave):
        awg_ctrl_reg, awg_wave_reg = dump_awg_all(awg_reg_access_i, target_awgs)
        if enable_awg_ctrl:
            print("---------------- AWG CTRL ----------------")
            show_registers(awg_ctrl_reg)
            print()
        if enable_awg_wave:
            print("---------------- AWG WAVE ----------------")
            show_registers(awg_wave_reg)
            print()

    if len(target_caps) > 0 and (enable_cap_ctrl or enable_cap_param or enable_cap_param_vector):
        cap_ctrl_reg, cap_param_reg, cap_param_vector = dump_cap_all(cap_reg_access_i,
                                                                     target_caps,
                                                                     enable_cap_param_vector)
        if enable_cap_ctrl:
            print("---------------- CAP CTRL ----------------")
            show_registers(cap_ctrl_reg)
            print()
        if enable_cap_param:
            print("---------------- CAP PARAM ----------------")
            show_registers(cap_param_reg)
            print()
        if enable_cap_param_vector:
            print("---------------- CAP VECTORS ----------------")
            show_vectors_complex(cap_param_vector)
