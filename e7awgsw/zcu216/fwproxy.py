import socket, struct
from ..hwdefs import E7AwgHwType
from ..hwparam import AwgParams, WaveRamParams
from ..rfdccommon.rftcmd import RftoolCommand
from ..rfdccommon.rftooltransceiver import RftoolTransceiver


def configure_fpga(transceiver: RftoolTransceiver, design_type: E7AwgHwType):
    """FPGA をコンフィギュレーションする"""
    if design_type != E7AwgHwType.ZCU216:
        raise ValueError(f"The HW type {design_type} is not for ZCU216.")

    type_to_id = { E7AwgHwType.ZCU216 : 19 }
    RftoolCommand(transceiver.ctrl_if).ConfigFpga(type_to_id[design_type], 25)


def enable_packet_forwarding(transceiver: RftoolTransceiver, design_type: E7AwgHwType):
    """ZCU216 のファームウェアのパケットフォワーディングを有効化する

    | パケットフォワーディングを有効にすると, 本来 FPGA の IP アドレスを指定して FPGA と受け渡しするパケットを
    | ZCU216 の IP アドレスを指定して受け渡しできるようになる.

    Args:
        transceiver (RftoolTransceiver): ZCU216 のファームウェアとの通信機能を提供するオブジェクト
        design_type (E7AwgHwType): e7awg_hw の種類
    """
    if design_type != E7AwgHwType.ZCU216:
        raise ValueError(f"The HW type {design_type} is not for ZCU216.")
    
    ip_addr = struct.unpack(">L", socket.inet_aton(transceiver.ip_addr))[0]
    ports = [
        WaveRamParams.of(design_type).udp_port(),
        AwgParams.of(design_type).udp_port()
    ]
    RftoolCommand(transceiver.ctrl_if).StartUdpForwarding(5, ip_addr, ports)


def disable_packet_forwarding(transceiver: RftoolTransceiver):
    """ZCU216 のファームウェアのパケットフォワーディングを無効化する
    
    Args:
        transceiver (RftoolTransceiver): ZCU216 のファームウェアとの通信機能を提供するオブジェクト
    """
    RftoolCommand(transceiver.ctrl_if).StopUdpForwarding(5)
