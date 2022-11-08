import sys
import pathlib
import argparse
from collections import OrderedDict
from typing import Any, List, Tuple, Set, Optional, cast

lib_path = str(pathlib.Path(__file__).resolve().parents[2])
sys.path.append(lib_path)
from e7awgsw import AWG, CaptureUnit
from e7awgsw.udpaccess import RegAccess, AwgRegAccess, CaptureRegAccess
from e7awgsw.hwparam import AWG_REG_PORT, CAPTURE_REG_PORT
from e7awgsw.memorymap import AwgMasterCtrlRegs, AwgCtrlRegs, WaveParamRegs, \
    CaptureMasterCtrlRegs, CaptureCtrlRegs, CaptureParamRegs

DEFAULT_IPADDR = '10.0.0.16'
NUM_CHUNKS = 16


def _convert_to_reg_list(reg_map: Any, cond: Optional[Set[str]] = None) -> List[Tuple[int, str]]:
    return sorted([(v, k) for k, v in reg_map.Offset.__dict__.items()
                   if k[0] != '_' and isinstance(v, int) and (cond is None or k in cond)])


def _dump_register_file(reg_access: RegAccess, base_addr: int, reg_list: List[Tuple[int, str]]) -> OrderedDict:
    reg_value = OrderedDict()
    for offset, name in reg_list:
        reg_value[name] = reg_access.read(base_addr, offset)
    return reg_value


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


def dump_awg_all(awg_reg_access: AwgRegAccess) -> Tuple[OrderedDict, OrderedDict]:
    ctrl = dump_awg_ctrl_master(awg_reg_access)
    wave = OrderedDict()
    for awg_id in AWG.all():
        ctrl[f"AWG_{awg_id:02d}"] = dump_awg_ctrl(awg_reg_access, awg_id)
        wave[f"AWG_{awg_id:02d}"] = dump_wave_param(awg_reg_access, awg_id)
    return ctrl, wave


def show(reg_values: OrderedDict, indent_unit: int = 4, indent_level: int = 0) -> None:
    indent = indent_unit * indent_level
    for k, v in reg_values.items():
        if isinstance(v, int):
            print(f"{' '*indent:s}{k:<20s}:\t{v:08x}")
        elif isinstance(v, OrderedDict):
            print(f"{' '*indent:s}{k+':':<20s}")
            show(v, indent_unit, indent_level+1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--ipaddr', type=str, default=DEFAULT_IPADDR)
    args = parser.parse_args()

    awg_reg_access_i = AwgRegAccess(args.ipaddr, AWG_REG_PORT)
    cap_reg_access_i = CaptureRegAccess(args.ipaddr, CAPTURE_REG_PORT)

    ctrl, wave = dump_awg_all(awg_reg_access_i)
    print("---------------- AWG CTRL ----------------")
    show(ctrl)
    print()
    print("---------------- AWG WAVE ----------------")
    show(wave)
