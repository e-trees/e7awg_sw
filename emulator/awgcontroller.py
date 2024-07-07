from __future__ import annotations

from awg import Awg
from typing import Final, Callable, Any
from collections.abc import Sequence, Mapping
from register import RwRegister, RoRegister
from e7awgsw import AWG
from e7awgsw.memorymap import AwgMasterCtrlRegs, AwgCtrlRegs, WaveParamRegs
from e7awgsw.logger import get_file_logger, get_stderr_logger, log_error


class AwgController(object):

    __NUM_REG_BITS: Final = 32

    def __init__(self) -> None:
        self.__awgs: dict[AWG, Awg] = {}
        self.__awg_ctrl_regs: dict[int, RoRegister | RwRegister] = {}
        self.__awg_master_ctrl_regs: dict[int, RoRegister | RwRegister] = {
            AwgMasterCtrlRegs.Offset.VERSION : self.__gen_version_reg(),
            AwgMasterCtrlRegs.Offset.CTRL_TARGET_SEL : RwRegister(self.__NUM_REG_BITS, 0),
            AwgMasterCtrlRegs.Offset.CTRL : self.__gen_master_ctrl_reg(),
            AwgMasterCtrlRegs.Offset.WAKEUP_STATUS : RoRegister(self.__NUM_REG_BITS),
            AwgMasterCtrlRegs.Offset.BUSY_STATUS : RoRegister(self.__NUM_REG_BITS),
            AwgMasterCtrlRegs.Offset.READY_STATUS : RoRegister(self.__NUM_REG_BITS),
            AwgMasterCtrlRegs.Offset.DONE_STATUS : RoRegister(self.__NUM_REG_BITS),
            AwgMasterCtrlRegs.Offset.READ_ERR : RoRegister(self.__NUM_REG_BITS),
            AwgMasterCtrlRegs.Offset.SAMPLE_SHORTAGE_ERR : RoRegister(self.__NUM_REG_BITS)
        }
        self.__actions_on_wave_generated: list[
            Callable[[Mapping[AWG, Sequence[tuple[int, int]]]], None]] = []
        self.__loggers = [get_file_logger(), get_stderr_logger()]


    def add_awg(self, awg: Awg) -> None:
        self.__awgs[awg.id] = awg
        base_addr = AwgCtrlRegs.Addr.awg(awg.id)
        self.__awg_ctrl_regs[base_addr + AwgCtrlRegs.Offset.CTRL] = self.__gen_ctrl_reg(awg)
        self.__awg_ctrl_regs[base_addr + AwgCtrlRegs.Offset.STATUS] = self.__gen_status_reg(awg)
        self.__awg_ctrl_regs[base_addr + AwgCtrlRegs.Offset.ERR] = RoRegister(self.__NUM_REG_BITS)
        self.__add_on_master_ctrl_write(awg.id, awg)
        self.__add_on_master_status_read(awg.id, awg)


    def write_reg(self, addr: int, val: int) -> None:
        # 波形パラメータ書き込み
        if self.__write_wave_param(addr, val):
            return

        # 個別コントロールレジスタ書き込み
        if self.__write_ctrl_reg(addr, val):
            return

        # 全体コントロールレジスタ書き込み
        master_ctrl_reg = self.__awg_master_ctrl_regs[addr]
        if (master_ctrl_reg is not None) and isinstance(master_ctrl_reg, RwRegister):
            master_ctrl_reg.set(val)
            return

        msg = 'Tried to write invalid AWG reg addr 0x{:x}'.format(addr)
        log_error(msg, *self.__loggers)
        raise ValueError(msg)


    def read_reg(self, addr: int) -> int:
        # 波形パラメータ読み出し
        val = self.__read_wave_param(addr)
        if val is not None:
            return val

        # 個別コントロールレジスタ読み出し
        val = self.__read_ctrl_reg(addr)
        if val is not None:
            return val

        # 全体コントロールレジスタ読み出し
        master_ctrl_reg = self.__awg_master_ctrl_regs[addr]
        if master_ctrl_reg is not None:
            return master_ctrl_reg.get()

        msg = 'Tried to read invalid AWG reg addr 0x{:x}'.format(addr)
        log_error(msg, *self.__loggers)
        raise ValueError(msg)


    def add_on_wave_generated(
        self,
        action: Callable[[Mapping[AWG, Sequence[tuple[int, int]]]], None]
    ) -> None:
        """AWG が波形を出力した際のイベントハンドラを登録する"""
        self.__actions_on_wave_generated.append(action)


    def __gen_ctrl_reg(self, awg: Awg) -> RwRegister:
        """個別コントロールレジスタを作成する"""
        ctrl_reg = RwRegister(self.__NUM_REG_BITS, 0)
        ctrl_reg.add_on_change(
            lambda old_bits, new_bits: self.__ctrl_reset(awg, True, new_bits[0]),
            AwgCtrlRegs.Bit.CTRL_RESET
        )
        ctrl_reg.add_on_change(
            lambda old_bits, new_bits: self.__ctrl_terminate(awg, True, old_bits[0], new_bits[0]),
            AwgCtrlRegs.Bit.CTRL_TERMINATE
        )
        ctrl_reg.add_on_change(
            lambda old_bits, new_bits: self.__ctrl_start(awg, old_bits[0], new_bits[0]),
            AwgCtrlRegs.Bit.CTRL_START
        )
        ctrl_reg.add_on_change(
            lambda old_bits, new_bits: self.__ctrl_prepare(awg, True, old_bits[0], new_bits[0]),
            AwgCtrlRegs.Bit.CTRL_PREPARE
        )
        ctrl_reg.add_on_change(
            lambda old_bits, new_bits: self.__ctrl_done_clr(awg, True, old_bits[0], new_bits[0]),
            AwgCtrlRegs.Bit.CTRL_DONE_CLR
        )
        return ctrl_reg


    def __gen_status_reg(self, awg: Awg) -> RoRegister:
        """個別ステータスレジスタを作成する"""
        status_reg = RoRegister(self.__NUM_REG_BITS)
        status_reg.add_on_read(
            lambda: [awg.is_wakeup()],
            AwgCtrlRegs.Bit.STATUS_WAKEUP
        )
        status_reg.add_on_read(
            lambda: [awg.is_busy()],
            AwgCtrlRegs.Bit.STATUS_BUSY
        )
        status_reg.add_on_read(
            lambda: [awg.is_ready()],
            AwgCtrlRegs.Bit.STATUS_READY
        )
        status_reg.add_on_read(
            lambda: [awg.is_complete()],
            AwgCtrlRegs.Bit.STATUS_DONE
        )
        return status_reg


    def __add_on_master_ctrl_write(self, awg_id: AWG, awg: Awg) -> None:
        """マスタコントロールレジスタの書き込み時のイベントハンドラを設定する"""
        bit_idx = AwgMasterCtrlRegs.Bit.awg(awg_id)
        ctrl_target_sel_reg = self.__awg_master_ctrl_regs[AwgMasterCtrlRegs.Offset.CTRL_TARGET_SEL]
        master_ctrl_reg: Any = self.__awg_master_ctrl_regs[AwgMasterCtrlRegs.Offset.CTRL]
        master_ctrl_reg.add_on_change(
            lambda old_bits, new_bits: self.__ctrl_reset(
                awg, ctrl_target_sel_reg.get_bit(bit_idx), new_bits[0]),
            AwgMasterCtrlRegs.Bit.CTRL_RESET
        )
        master_ctrl_reg.add_on_change(
            lambda old_bits, new_bits: self.__ctrl_terminate(
                awg, ctrl_target_sel_reg.get_bit(bit_idx), old_bits[0], new_bits[0]),
            AwgMasterCtrlRegs.Bit.CTRL_TERMINATE
        )
        master_ctrl_reg.add_on_change(
            lambda old_bits, new_bits: self.__ctrl_prepare(
                awg, ctrl_target_sel_reg.get_bit(bit_idx), old_bits[0], new_bits[0]),
            AwgMasterCtrlRegs.Bit.CTRL_PREPARE
        )
        master_ctrl_reg.add_on_change(
            lambda old_bits, new_bits: self.__ctrl_done_clr(
                awg, ctrl_target_sel_reg.get_bit(bit_idx), old_bits[0], new_bits[0]),
            AwgMasterCtrlRegs.Bit.CTRL_DONE_CLR
        )


    def __add_on_master_status_read(self, awg_id: AWG, awg: Awg) -> None:
        """マスタステータスレジスタのステータス読み取り時のイベントハンドラを設定する"""
        bit_idx = AwgMasterCtrlRegs.Bit.awg(awg_id)
        ctrl_target_sel_reg = self.__awg_master_ctrl_regs[AwgMasterCtrlRegs.Offset.CTRL_TARGET_SEL]
        master_wakeup_reg: Any = self.__awg_master_ctrl_regs[AwgMasterCtrlRegs.Offset.WAKEUP_STATUS]
        master_wakeup_reg.add_on_read(
            lambda: [awg.is_wakeup() & ctrl_target_sel_reg.get_bit(bit_idx)],
            bit_idx
        )
        master_busy_reg: Any = self.__awg_master_ctrl_regs[AwgMasterCtrlRegs.Offset.BUSY_STATUS]
        master_busy_reg.add_on_read(
            lambda: [awg.is_busy() & ctrl_target_sel_reg.get_bit(bit_idx)],
            bit_idx
        )
        master_ready_reg: Any = self.__awg_master_ctrl_regs[AwgMasterCtrlRegs.Offset.READY_STATUS]
        master_ready_reg.add_on_read(
            lambda: [awg.is_ready() & ctrl_target_sel_reg.get_bit(bit_idx)],
            bit_idx
        )
        master_done_reg: Any = self.__awg_master_ctrl_regs[AwgMasterCtrlRegs.Offset.DONE_STATUS]
        master_done_reg.add_on_read(
            lambda: [awg.is_complete() & ctrl_target_sel_reg.get_bit(bit_idx)],
            bit_idx
        )


    def __ctrl_reset(self, awg: Awg, is_ctrl_target: int, new_val: int) -> None:
        if is_ctrl_target:
            if new_val == 1:
                awg.assert_reset()
            if new_val == 0:
                awg.deassert_reset()


    def __ctrl_terminate(
        self, awg: Awg, is_ctrl_target: int, old_val: int, new_val: int
    ) -> None:
        if is_ctrl_target and (old_val == 0) and (new_val == 1):
            awg.terminate()


    def __ctrl_start(self, awg: Awg, old_val: int, new_val: int) -> None:
        """個別コントロールレジスタのスタートビット変更時の処理"""
        if (old_val == 0) and (new_val == 1):
            is_wave_generated, wave  = awg.generate_wave()
            if is_wave_generated:
                for action in self.__actions_on_wave_generated:
                    action({awg.id : wave})


    def __ctrl_master_start(self, old_val: int, new_val: int) -> None:
        """マスターコントロールレジスタのスタートビット変更時の処理"""
        if (old_val == 0) and (new_val == 1):
            awg_id_to_wave = {}
            for awg in self.__awgs.values():
                ctrl_target_reg = self.__awg_master_ctrl_regs[AwgMasterCtrlRegs.Offset.CTRL_TARGET_SEL]
                if ctrl_target_reg.get_bit(AwgMasterCtrlRegs.Bit.awg(awg.id)):
                    is_wave_generated, wave  = awg.generate_wave()
                    if is_wave_generated:
                        awg_id_to_wave[awg.id] = wave
            
            for action in self.__actions_on_wave_generated:
                action(awg_id_to_wave)


    def __ctrl_prepare(
        self, awg: Awg, is_ctrl_target: int, old_val: int, new_val: int
    ) -> None:
        if is_ctrl_target and (old_val == 0) and (new_val == 1):
            awg.preload()


    def __ctrl_done_clr(
        self, awg: Awg, is_ctrl_target: int, old_val: int, new_val: int
    ) -> None:
        if is_ctrl_target and (old_val == 0) and (new_val == 1):
            awg.set_to_idle()


    def __gen_version_reg(self) -> RoRegister:
        char = 'K'
        year = 22
        month = 3
        day = 15
        id = 1
        version  = (ord(char) & 0xFF) << 24
        version |= (year      & 0xFF) << 16
        version |= (month     & 0xF)  << 12
        version |= (day       & 0xFF) << 4
        version |= (id        & 0xF)
        return RoRegister(self.__NUM_REG_BITS, val = version)


    def __gen_master_ctrl_reg(self) -> RwRegister:
        master_ctrl_reg = RwRegister(self.__NUM_REG_BITS, 0)
        master_ctrl_reg.add_on_change(
            lambda old_bits, new_bits: self.__ctrl_master_start(old_bits[0], new_bits[0]),
            AwgMasterCtrlRegs.Bit.CTRL_START
        )
        return master_ctrl_reg


    def __write_wave_param(self, addr: int, val: int) -> bool:
        """波形パラメータ書き込み"""
        awg_id_list = reversed(AWG.all())
        for awg_id in awg_id_list:
            param_base_addr = WaveParamRegs.Addr.awg(awg_id)
            if addr >= param_base_addr:
                if awg_id in self.__awgs:
                    self.__awgs[awg_id].set_param(addr - param_base_addr, val)
                return True
        return False


    def __write_ctrl_reg(self, addr: int, val: int) -> bool:
        """個別コントロールレジスタ書き込み"""
        ctrl_reg = self.__awg_ctrl_regs.get(addr)
        if (ctrl_reg is not None) and isinstance(ctrl_reg, RwRegister):
            ctrl_reg.set(val)
            return True
        return False


    def __read_wave_param(self, addr: int) -> int | None:
        """波形パラメータ読み出し"""
        awg_id_list = reversed(AWG.all())
        for awg_id in awg_id_list:
            param_base_addr = WaveParamRegs.Addr.awg(awg_id)
            if addr >= param_base_addr:
                if awg_id in self.__awgs:
                    return self.__awgs[awg_id].get_param(addr - param_base_addr)
        return None


    def __read_ctrl_reg(self, addr: int) -> int | None:
        """個別コントロールレジスタ読み出し"""
        ctrl_reg = self.__awg_ctrl_regs.get(addr)
        if ctrl_reg is not None:
            return ctrl_reg.get()
        return None
