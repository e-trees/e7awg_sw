
class AwgTimeoutError(Exception):
    pass

class CaptureUnitTimeoutError(Exception):
    pass

class UnsupportedOperationError(Exception):
    """未サポートの処理を実行するメソッドを呼んだときの例外"""

    def __init__(self, msg=''):
        self.__msg = str(msg)

    def __str__(self):
        return self.__msg
