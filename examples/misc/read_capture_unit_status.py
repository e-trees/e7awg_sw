# デバッグ用スクリプト
import argparse
from e7awgsw import CaptureUnit
from e7awgsw.udpaccess import CaptureRegAccess
from e7awgsw.hwparam import CAPTURE_REG_PORT
from e7awgsw.memorymap import CaptureCtrlRegs

IP_ADDR = '10.0.0.16'

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--ipaddr')
    args = parser.parse_args()
    
    if args.ipaddr is not None:
        IP_ADDR = args.ipaddr

    # 通常 CaptureRegAccess は使用しないこと
    cap_reg_access = CaptureRegAccess(IP_ADDR, CAPTURE_REG_PORT)
    for capture_unit_id in CaptureUnit.all():
        base_addr = CaptureCtrlRegs.Addr.capture(capture_unit_id)
        wakeup = cap_reg_access.read_bits(
            base_addr, CaptureCtrlRegs.Offset.STATUS, CaptureCtrlRegs.Bit.STATUS_WAKEUP, 1)
        busy = cap_reg_access.read_bits(
            base_addr, CaptureCtrlRegs.Offset.STATUS, CaptureCtrlRegs.Bit.STATUS_BUSY, 1)
        done = cap_reg_access.read_bits(
            base_addr, CaptureCtrlRegs.Offset.STATUS, CaptureCtrlRegs.Bit.STATUS_DONE, 1)
        fifo_overflow = cap_reg_access.read_bits(
            base_addr, CaptureCtrlRegs.Offset.ERR, CaptureCtrlRegs.Bit.ERR_OVERFLOW, 1)
        write_err = cap_reg_access.read_bits(
            base_addr, CaptureCtrlRegs.Offset.ERR, CaptureCtrlRegs.Bit.ERR_WRITE, 1)
        print('capture unit {}'.format(capture_unit_id))
        print('  wakeup : {}'.format(wakeup))
        print('  busy : {}'.format(busy))
        print('  done : {}'.format(done))
        print('  fifo_overflow : {}'.format(fifo_overflow))
        print('  write_err : {}\n'.format(write_err))
