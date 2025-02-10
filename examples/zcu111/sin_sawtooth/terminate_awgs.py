import argparse
import e7awgsw as e7s
import e7awgsw.zcu111 as e7sz

def main(design_type):
    fpga_ip_addr = '10.0.0.16'
    with (e7s.AwgCtrl(fpga_ip_addr, design_type) as awg_ctrl):
        print('terminate AWGs')
        awg_ctrl.terminate_awgs(*e7s.AWG.on(design_type))

if __name__ == "__main__":
    main(e7s.E7AwgHwType.ZCU111_DAC_6G_URAM_X2)
