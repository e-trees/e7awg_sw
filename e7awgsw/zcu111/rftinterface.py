from ..logger import get_null_logger, log_error
from .rfterr import RftoolExecuteCommandError

"""
rftinterface.py
    - RFTOOLs command / data communication interface
"""

class RftoolInterface(object):
    def __init__(self, *loggers):
        self._loggers = loggers
        self.sock = None
        self.err_connection = False

    def attach_socket(self, sock):
        self.sock = sock

    def send_command(self, cmd):
        cmd_bytes = cmd.encode() + b"\r\n"
        try:
            self.sock.sendall(cmd_bytes)
        except Exception as e:
            log_error("send command err: {}\n".format(cmd), *self._loggers)
            self.err_connection = True
            raise

    def recv_response(self):
        res = b""
        try:
            while res[-1:] != b"\n":
                res += self.sock.recv(1)
        except Exception as e:
            log_error("recv response err: {}\n".format(res), *self._loggers)
            self.err_connection = True
            raise
        res = res.decode()
        return res

    def put(self, command):
        self.send_command(command)
        res = self.recv_response().replace("\r\n", "")
        if res[:5] == "ERROR":
            self.send_command("GetLog")
            log = self.recv_response().replace("\r\n", "")
            raise RftoolExecuteCommandError("\n".join([command, res, log[6:]]))

        return res
