import argparse
from e7awgsw import AWG, AwgCtrl, E7AwgHwType
from e7awgsw.labrad import RemoteAwgCtrl

IP_ADDR = '10.0.0.16'

def create_awg_ctrl(use_labrad, server_ip_addr):
    if use_labrad:
        return RemoteAwgCtrl(server_ip_addr, IP_ADDR, E7AwgHwType.SIMPLE_MULTI)
    else:
        return AwgCtrl(IP_ADDR, E7AwgHwType.SIMPLE_MULTI)

def main(awgs, use_labrad, server_ip_addr):
    with (create_awg_ctrl(use_labrad, server_ip_addr) as awg_ctrl):
        # 初期化
        awg_ctrl.initialize(*awgs)
        awg_ctrl.reset_awgs(*awgs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--ipaddr')
    parser.add_argument('--awgs')
    parser.add_argument('--server_ipaddr')
    parser.add_argument('--labrad', action='store_true')
    args = parser.parse_args()

    if args.ipaddr is not None:
        IP_ADDR = args.ipaddr

    awgs = sorted(AWG.on(E7AwgHwType.SIMPLE_MULTI))
    if args.awgs is not None:
        awgs = [AWG.of(int(x)) for x in args.awgs.split(',')]

    main(awgs, args.labrad, args.server_ipaddr)
