import argparse
from e7awgsw import AwgCtrl, CaptureCtrl, CaptureUnit, CaptureModule, AWG
from e7awgsw.labrad import RemoteAwgCtrl, RemoteCaptureCtrl

IP_ADDR = '10.0.0.16'
CAP_MOD_TO_UNITS = {
    CaptureModule.U0 : [CaptureUnit.U0, CaptureUnit.U1, CaptureUnit.U2, CaptureUnit.U3],
    CaptureModule.U1 : [CaptureUnit.U4, CaptureUnit.U5, CaptureUnit.U6, CaptureUnit.U7],
    CaptureModule.U2 : [CaptureUnit.U8],
    CaptureModule.U3 : [CaptureUnit.U9]
}

def create_awg_ctrl(use_labrad, server_ip_addr):
    if use_labrad:
        return RemoteAwgCtrl(server_ip_addr, IP_ADDR)
    else:
        return AwgCtrl(IP_ADDR)


def create_capture_ctrl(use_labrad, server_ip_addr):
    if use_labrad:
        return RemoteCaptureCtrl(server_ip_addr, IP_ADDR)
    else:
        return CaptureCtrl(IP_ADDR)


def main(do_init, awgs, capture_modules, use_labrad, server_ip_addr):
    capture_units = [CAP_MOD_TO_UNITS[cap_mod] for cap_mod in capture_modules]
    capture_units = sum(capture_units, []) # flatten
    with (create_awg_ctrl(use_labrad, server_ip_addr) as awg_ctrl,
          create_capture_ctrl(use_labrad, server_ip_addr) as cap_ctrl):
        # 初期化 (リセット含む)
        if do_init:
            awg_ctrl.initialize(*awgs)
            cap_ctrl.initialize(*capture_units)
        # リセットだけ
        else:
            awg_ctrl.reset_awgs(*awgs)
            cap_ctrl.reset_capture_units(*capture_units)
        print('end')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--init', action='store_true')
    parser.add_argument('--ipaddr')
    parser.add_argument('--awgs')
    parser.add_argument('--capture-module')
    parser.add_argument('--server-ipaddr')
    parser.add_argument('--labrad', action='store_true')
    args = parser.parse_args()

    if args.ipaddr is not None:
        IP_ADDR = args.ipaddr

    awgs = AWG.all()
    if args.awgs is not None:
        awgs = [AWG.of(int(x)) for x in args.awgs.split(',')]

    capture_modules = CaptureModule.all()
    if args.capture_module is not None:
        capture_modules = [CaptureModule.of(int(args.capture_module))]

    server_ip_addr = 'localhost'
    if args.server_ipaddr is not None:
        server_ip_addr = args.server_ipaddr

    main(args.init, awgs, capture_modules, args.labrad, server_ip_addr)
