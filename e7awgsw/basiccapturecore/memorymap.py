from typing import Final

class CaptureMasterCtrlRegs(object):
    ADDR: Final = 0x20_0000

    class Offset(object):
        VERSION: Final            = 0x0
        CTRL_TARGET_SEL: Final    = 0x4
        CTRL: Final               = 0x8

    class Bit(object):
        CTRL_RESET: Final     = 0
        CTRL_START: Final     = 1
        CTRL_TERMINATE: Final = 2
        CTRL_DONE_CLR: Final  = 3


class CaptureCtrlRegs(object):

    class Addr(object):
        CAPTURE_0: Final  = 0x20_0100
        CAPTURE_1: Final  = 0x20_0200
        CAPTURE_2: Final  = 0x20_0300
        CAPTURE_3: Final  = 0x20_0400
        CAPTURE_4: Final  = 0x20_0500
        CAPTURE_5: Final  = 0x20_0600
        CAPTURE_6: Final  = 0x20_0700
        CAPTURE_7: Final  = 0x20_0800

        __LIST: Final = [
            CAPTURE_0, CAPTURE_1, CAPTURE_2, CAPTURE_3,
            CAPTURE_4, CAPTURE_5, CAPTURE_6, CAPTURE_7]

        @classmethod
        def capture(cls, idx: int) -> int:
            return cls.__LIST[idx]


    class Offset(object):
        CTRL: Final            = 0x0
        STATUS: Final          = 0x4
        ERR: Final             = 0x8
        START_TRIG_MASK: Final = 0xC

    class Bit(object):
        CTRL_RESET: Final     = 0
        CTRL_START: Final     = 1
        CTRL_TERMINATE: Final = 2
        CTRL_DONE_CLR: Final  = 3
        STATUS_WAKEUP: Final  = 0
        STATUS_BUSY: Final    = 1
        STATUS_DONE: Final    = 2
        ERR_OVERFLOW: Final   = 0
        ERR_WRITE: Final      = 1


class CaptureParamRegs(object):
    #### capture params ####
    class Addr(object):
        CAPTURE_0: Final  = 0x21_0000
        CAPTURE_1: Final  = 0x22_0000
        CAPTURE_2: Final  = 0x23_0000
        CAPTURE_3: Final  = 0x24_0000
        CAPTURE_4: Final  = 0x25_0000
        CAPTURE_5: Final  = 0x26_0000
        CAPTURE_6: Final  = 0x27_0000
        CAPTURE_7: Final  = 0x28_0000

        __LIST: Final = [
            CAPTURE_0, CAPTURE_1, CAPTURE_2, CAPTURE_3,
            CAPTURE_4, CAPTURE_5, CAPTURE_6, CAPTURE_7]

        @classmethod
        def capture(cls, idx: int) -> int:
            return cls.__LIST[idx]

    class Offset(object):

        DSP_MODULE_ENABLE: Final       = 0x0
        CAPTURE_DATA_TYPE: Final       = 0x4
        CAPTURE_DELAY: Final           = 0x8
        CAPTURE_ADDR: Final            = 0xC
        NUM_CAPTURED_SAMPLES: Final    = 0x10
        NUM_CAPTURE_STEPS: Final       = 0x14
        NUM_SUM_WORDS: Final           = 0x9000
        I_OR_REAL_BIN_THRESHOLD: Final = 0x9004
        Q_BIN_THRESHOLD: Final         = 0x9008
        I_OR_REAL_REDUCTION_OP: Final  = 0x900C
        Q_REDUCTION_OP: Final          = 0x9010

        __MAX_CAP_STEPS: Final = 1024

        @classmethod
        def cap_target_len(cls, idx: int) -> int:
            if idx >= cls.__MAX_CAP_STEPS:
                raise ValueError("capture target length addr offset error")
            CAP_TARGET_LEN_OFFSET = 0x1000
            return 4 * idx + CAP_TARGET_LEN_OFFSET

        @classmethod
        def post_blank_len(cls, idx: int) -> int:
            if idx >= cls.__MAX_CAP_STEPS:
                raise ValueError("post blank length addr offset error")
            POST_BLANK_LEN_OFFSET = 0x5000
            return 4 * idx + POST_BLANK_LEN_OFFSET
