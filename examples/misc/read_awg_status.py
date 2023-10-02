# デバッグ用スクリプト
import argparse
from e7awgsw import AWG
from e7awgsw.udpaccess import AwgRegAccess
from e7awgsw.hwparam import AWG_REG_PORT
from e7awgsw.memorymap import AwgCtrlRegs

IP_ADDR = '10.0.0.16'

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--ipaddr')
    args = parser.parse_args()
    
    if args.ipaddr is not None:
        IP_ADDR = args.ipaddr

    # 通常 AwgRegAccess は使用しないこと
    awg_reg_access = AwgRegAccess(IP_ADDR, AWG_REG_PORT)
    for awg_id in AWG.all():
        base_addr = AwgCtrlRegs.Addr.awg(awg_id)
        wakeup = awg_reg_access.read_bits(
            base_addr, AwgCtrlRegs.Offset.STATUS, AwgCtrlRegs.Bit.STATUS_WAKEUP, 1)
        busy = awg_reg_access.read_bits(
            base_addr, AwgCtrlRegs.Offset.STATUS, AwgCtrlRegs.Bit.STATUS_BUSY, 1)
        ready = awg_reg_access.read_bits(
            base_addr, AwgCtrlRegs.Offset.STATUS, AwgCtrlRegs.Bit.STATUS_READY, 1)
        done = awg_reg_access.read_bits(
            base_addr, AwgCtrlRegs.Offset.STATUS, AwgCtrlRegs.Bit.STATUS_DONE, 1)
        read_err = awg_reg_access.read_bits(
            base_addr, AwgCtrlRegs.Offset.ERR, AwgCtrlRegs.Bit.ERR_READ, 1)
        sample_shortage = awg_reg_access.read_bits(
            base_addr, AwgCtrlRegs.Offset.ERR, AwgCtrlRegs.Bit.ERR_SAMPLE_SHORTAGE, 1)
        print('awg {}'.format(awg_id))
        print('  wakeup : {}'.format(wakeup))
        print('  busy : {}'.format(busy))
        print('  ready : {}'.format(ready))
        print('  done : {}'.format(done))
        print('  read_err : {}'.format(read_err))
        print('  sample_shortage : {}\n'.format(sample_shortage))
