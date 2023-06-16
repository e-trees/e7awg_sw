import sys
import pathlib
from register import RwRegister, RoRegister

lib_path = str(pathlib.Path(__file__).resolve().parents[1])
sys.path.append(lib_path)
from e7awgsw import CaptureUnit, CaptureModule
from e7awgsw.memorymap import CaptureMasterCtrlRegs, CaptureCtrlRegs, CaptureParamRegs
from e7awgsw.logger import get_file_logger, get_stderr_logger, log_error, log_warning


class CaptureController(object):

    __NUM_REG_BITS = 32
    __cap_unit_to_param_base_addr = { 
        cap_unit_id : CaptureParamRegs.Addr.capture(cap_unit_id) for cap_unit_id in CaptureUnit.all() }
    __cap_unit_to_ctrl_reg_base_addr = { 
        cap_unit_id : CaptureCtrlRegs.Addr.capture(cap_unit_id) for cap_unit_id in CaptureUnit.all() }

    def __init__(self):
        self.__cap_units = {}
        self.__capture_ctrl_regs = {}
        self.__capture_master_ctrl_regs = {
            CaptureMasterCtrlRegs.Offset.VERSION : self.__gen_version_reg(),
            CaptureMasterCtrlRegs.Offset.TRIG_AWG_SEL_0 : RwRegister(self.__NUM_REG_BITS, 0),
            CaptureMasterCtrlRegs.Offset.TRIG_AWG_SEL_1 : RwRegister(self.__NUM_REG_BITS, 0),
            CaptureMasterCtrlRegs.Offset.AWG_TRIG_MASK : RwRegister(self.__NUM_REG_BITS, 0),
            CaptureMasterCtrlRegs.Offset.CTRL_TARGET_SEL : RwRegister(self.__NUM_REG_BITS, 0),
            CaptureMasterCtrlRegs.Offset.CTRL : RwRegister(self.__NUM_REG_BITS, 0),
            CaptureMasterCtrlRegs.Offset.WAKEUP_STATUS : RoRegister(self.__NUM_REG_BITS),
            CaptureMasterCtrlRegs.Offset.BUSY_STATUS : RoRegister(self.__NUM_REG_BITS),
            CaptureMasterCtrlRegs.Offset.DONE_STATUS : RoRegister(self.__NUM_REG_BITS),
            CaptureMasterCtrlRegs.Offset.OVERFLOW_ERR : RoRegister(self.__NUM_REG_BITS),
            CaptureMasterCtrlRegs.Offset.WRITE_ERR : RoRegister(self.__NUM_REG_BITS),
            CaptureMasterCtrlRegs.Offset.TRIG_AWG_SEL_2 : RwRegister(self.__NUM_REG_BITS, 0),
            CaptureMasterCtrlRegs.Offset.TRIG_AWG_SEL_3 : RwRegister(self.__NUM_REG_BITS, 0)
        }
        self.__loggers = [get_file_logger(), get_stderr_logger()]


    def add_capture_unit(self, cap_unit):
        self.__cap_units[cap_unit.id] = cap_unit
        base_addr = self.__cap_unit_to_ctrl_reg_base_addr[cap_unit.id]
        self.__capture_ctrl_regs[base_addr + CaptureCtrlRegs.Offset.CTRL] = self.__gen_ctrl_reg(cap_unit)
        self.__capture_ctrl_regs[base_addr + CaptureCtrlRegs.Offset.STATUS] = self.__gen_status_reg(cap_unit)
        self.__capture_ctrl_regs[base_addr + CaptureCtrlRegs.Offset.ERR] = RoRegister(self.__NUM_REG_BITS)
        self.__add_on_master_ctrl_write(cap_unit.id, cap_unit)
        self.__add_on_master_status_read(cap_unit.id, cap_unit)


    def write_reg(self, addr, val):
        # 波形パラメータ書き込み
        if self.__write_capture_param(addr, val):
            return

        # 個別コントロールレジスタ書き込み
        if self.__write_ctrl_reg(addr, val):
            return

        # 全体コントロールレジスタ書き込み
        master_ctrl_reg = self.__capture_master_ctrl_regs.get(addr)
        if (master_ctrl_reg is not None) and isinstance(master_ctrl_reg, RwRegister):
            master_ctrl_reg.set(val)
            return

        msg = 'Tried to write invalid capture unit reg addr 0x{:x}'.format(addr)
        log_error(msg, *self.__loggers)
        raise ValueError(msg)


    def read_reg(self, addr):
        # 波形パラメータ読み出し
        val = self.__read_wave_param(addr)
        if val is not None:
            return val

        # 個別コントロールレジスタ読み出し
        val = self.__read_ctrl_reg(addr)
        if val is not None:
            return val

        # 全体コントロールレジスタ読み出し
        master_ctrl_reg = self.__capture_master_ctrl_regs.get(addr)
        if master_ctrl_reg is not None:
            return master_ctrl_reg.get()

        msg = 'Tried to read invalid capture unit reg addr 0x{:x}'.format(addr)
        log_error(msg, *self.__loggers)
        raise ValueError(msg)


    def on_wave_generated(self, awg_id_list, cap_mod_to_wave):
        """AWG が波形データを生成した時のイベントハンドラ
        Args:
            awg_id_list (AWG): 波形データを生成した AWG の ID
            cap_mod_to_wave ({CaptureModule : (int, int)}) : キャプチャモジュールの ID とそれに入力される波形データの dict
        """
        cap_mod_id_list = self.__get_cap_mod_to_start(awg_id_list)
        trig_mask_reg = self.__capture_master_ctrl_regs[CaptureMasterCtrlRegs.Offset.AWG_TRIG_MASK]
        for cap_mod_id in cap_mod_id_list:
            wave = cap_mod_to_wave[cap_mod_id]
            for cap_unit_id in CaptureModule.get_units(cap_mod_id):
                if (cap_unit_id in self.__cap_units) and trig_mask_reg.get_bit(cap_unit_id):
                    self.__cap_units[cap_unit_id].capture_wave(wave, is_async = True)


    def __get_cap_mod_to_start(self, awg_id_list):
        """AWG からのスタート信号によりスタートに対象となるキャプチャモジュールを取得する"""
        trig_awg_sel_0_reg = self.__capture_master_ctrl_regs[CaptureMasterCtrlRegs.Offset.TRIG_AWG_SEL_0]
        trig_awg_sel_1_reg = self.__capture_master_ctrl_regs[CaptureMasterCtrlRegs.Offset.TRIG_AWG_SEL_1]
        trig_awg_sel_2_reg = self.__capture_master_ctrl_regs[CaptureMasterCtrlRegs.Offset.TRIG_AWG_SEL_2]
        trig_awg_sel_3_reg = self.__capture_master_ctrl_regs[CaptureMasterCtrlRegs.Offset.TRIG_AWG_SEL_3]
        cap_mod_id_list = []        
        if (trig_awg_sel_0_reg.get() - 1) in awg_id_list:
            cap_mod_id_list.append(CaptureModule.U0)
        if (trig_awg_sel_1_reg.get() - 1) in awg_id_list:
            cap_mod_id_list.append(CaptureModule.U1)
        if (trig_awg_sel_2_reg.get() - 1) in awg_id_list:
            cap_mod_id_list.append(CaptureModule.U2)
        if (trig_awg_sel_3_reg.get() - 1) in awg_id_list:
            cap_mod_id_list.append(CaptureModule.U3)
        return cap_mod_id_list


    def __gen_ctrl_reg(self, cap_unit):
        ctrl_reg = RwRegister(self.__NUM_REG_BITS, 0)
        ctrl_reg.add_on_change(
            lambda old_bits, new_bits: self.__ctrl_reset(cap_unit, True, new_bits[0]),
            CaptureCtrlRegs.Bit.CTRL_RESET
        )
        ctrl_reg.add_on_change(
            lambda old_bits, new_bits: self.__ctrl_terminate(cap_unit, True, old_bits[0], new_bits[0]),
            CaptureCtrlRegs.Bit.CTRL_TERMINATE
        )
        ctrl_reg.add_on_change(
            lambda old_bits, new_bits: self.__ctrl_start(cap_unit, True, old_bits[0], new_bits[0]),
            CaptureCtrlRegs.Bit.CTRL_START
        )
        ctrl_reg.add_on_change(
            lambda old_bits, new_bits: self.__ctrl_done_clr(cap_unit, True, old_bits[0], new_bits[0]),
            CaptureCtrlRegs.Bit.CTRL_DONE_CLR
        )
        return ctrl_reg


    def __gen_status_reg(self, cap_unit):
        status_reg = RoRegister(self.__NUM_REG_BITS)
        status_reg.add_on_read(
            lambda: [cap_unit.is_wakeup()],
            CaptureCtrlRegs.Bit.STATUS_WAKEUP
        )
        status_reg.add_on_read(
            lambda: [cap_unit.is_busy()],
            CaptureCtrlRegs.Bit.STATUS_BUSY
        )
        status_reg.add_on_read(
            lambda: [cap_unit.is_complete()],
            CaptureCtrlRegs.Bit.STATUS_DONE
        )
        return status_reg


    def __add_on_master_ctrl_write(self, cap_unit_id, cap_unit):
        """マスタコントロールレジスタの書き込み時のイベントハンドラを設定する"""
        bit_idx = CaptureMasterCtrlRegs.Bit.capture(cap_unit_id)
        ctrl_target_sel_reg = self.__capture_master_ctrl_regs[CaptureMasterCtrlRegs.Offset.CTRL_TARGET_SEL]
        master_ctrl_reg = self.__capture_master_ctrl_regs[CaptureMasterCtrlRegs.Offset.CTRL]
        master_ctrl_reg.add_on_change(
            lambda old_bits, new_bits: self.__ctrl_reset(
                cap_unit, ctrl_target_sel_reg.get_bit(bit_idx), new_bits[0]),
            CaptureMasterCtrlRegs.Bit.CTRL_RESET
        )
        master_ctrl_reg.add_on_change(
            lambda old_bits, new_bits: self.__ctrl_terminate(
                cap_unit, ctrl_target_sel_reg.get_bit(bit_idx), old_bits[0], new_bits[0]),
            CaptureMasterCtrlRegs.Bit.CTRL_TERMINATE
        )
        master_ctrl_reg.add_on_change(
            lambda old_bits, new_bits: self.__ctrl_start(
                cap_unit, ctrl_target_sel_reg.get_bit(bit_idx), old_bits[0], new_bits[0]),
            CaptureMasterCtrlRegs.Bit.CTRL_START
        )
        master_ctrl_reg.add_on_change(
            lambda old_bits, new_bits: self.__ctrl_done_clr(
                cap_unit, ctrl_target_sel_reg.get_bit(bit_idx), old_bits[0], new_bits[0]),
            CaptureMasterCtrlRegs.Bit.CTRL_DONE_CLR
        )


    def __add_on_master_status_read(self, cap_unit_id, cap_unit):
        """マスタステータスレジスタのステータス読み取り時のイベントハンドラを設定する"""
        bit_idx = CaptureMasterCtrlRegs.Bit.capture(cap_unit_id)
        ctrl_target_sel_reg = self.__capture_master_ctrl_regs[CaptureMasterCtrlRegs.Offset.CTRL_TARGET_SEL]
        master_wakeup_reg = self.__capture_master_ctrl_regs[CaptureMasterCtrlRegs.Offset.WAKEUP_STATUS]
        master_wakeup_reg.add_on_read(
            lambda: [cap_unit.is_wakeup() & ctrl_target_sel_reg.get_bit(bit_idx)],
            bit_idx
        )
        master_busy_reg = self.__capture_master_ctrl_regs[CaptureMasterCtrlRegs.Offset.BUSY_STATUS]
        master_busy_reg.add_on_read(
            lambda: [cap_unit.is_busy() & ctrl_target_sel_reg.get_bit(bit_idx)],
            bit_idx
        )
        master_done_reg = self.__capture_master_ctrl_regs[CaptureMasterCtrlRegs.Offset.DONE_STATUS]
        master_done_reg.add_on_read(
            lambda: [cap_unit.is_complete() & ctrl_target_sel_reg.get_bit(bit_idx)],
            bit_idx
        )


    def __ctrl_reset(self, cap_unit, is_ctrl_target, new_val):
        if is_ctrl_target:
            if new_val == 1:
                cap_unit.assert_reset()
            if new_val == 0:
                cap_unit.diassert_reset()


    def __ctrl_terminate(self, cap_unit, is_ctrl_target, old_val, new_val):
        if is_ctrl_target and (old_val == 0) and (new_val == 1):
            cap_unit.terminate()


    def __ctrl_start(self, cap_unit, is_ctrl_target, old_val, new_val):
        if is_ctrl_target and (old_val == 0) and (new_val == 1):
            cap_unit.capture_wave([], is_async = True)


    def __ctrl_done_clr(self, cap_unit, is_ctrl_target, old_val, new_val):
        if is_ctrl_target and (old_val == 0) and (new_val == 1):
            cap_unit.set_to_idle()


    def __gen_version_reg(self):
        char = 'K'
        year = 22
        month = 3
        day = 15
        id = 2
        version  = (ord(char) & 0xFF) << 24
        version |= (year      & 0xFF) << 16
        version |= (month     & 0xF)  << 12
        version |= (day       & 0xFF) << 4
        version |= (id        & 0xF)
        return RoRegister(self.__NUM_REG_BITS, val = version)


    def __write_capture_param(self, addr, val):
        """キャプチャパラメータ書き込み"""
        cap_unit_id_list = reversed(CaptureUnit.all())
        for cap_unit_id in cap_unit_id_list:
            param_base_addr = self.__cap_unit_to_param_base_addr[cap_unit_id]
            if addr >= param_base_addr:
                if cap_unit_id in self.__cap_units:
                    self.__cap_units[cap_unit_id].set_param(addr - param_base_addr, val)
                return True


    def __write_ctrl_reg(self, addr, val):
        """個別コントロールレジスタ書き込み"""
        ctrl_reg = self.__capture_ctrl_regs.get(addr)
        if (ctrl_reg is not None) and isinstance(ctrl_reg, RwRegister):
            ctrl_reg.set(val)
            return True


    def __read_wave_param(self, addr):
        """キャプチャパラメータ読み出し"""
        cap_unit_id_list = reversed(CaptureUnit.all())
        for cap_unit_id in cap_unit_id_list:
            param_base_addr = self.__cap_unit_to_param_base_addr[cap_unit_id]
            if addr >= param_base_addr:
                if cap_unit_id in self.__cap_units:
                    return self.__cap_units[cap_unit_id].get_param(addr - param_base_addr)


    def __read_ctrl_reg(self, addr):
        """個別コントロールレジスタ読み出し"""
        ctrl_reg = self.__capture_ctrl_regs.get(addr)
        if ctrl_reg is not None:
            return ctrl_reg.get()
