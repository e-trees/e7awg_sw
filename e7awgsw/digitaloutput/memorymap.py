from typing import Final

class DigitalOutMasterCtrlRegs(object):
    ADDR: Final = 0

    class Offset(object):
        VERSION: Final             = 0x0
        CTRL_TARGET_SEL_0: Final   = 0x4
        CTRL_TARGET_SEL_1: Final   = 0x8
        CTRL: Final                = 0xC
        START_TRIG_MASK_0: Final   = 0x10
        START_TRIG_MASK_1: Final   = 0x14
        RESTART_TRIG_MASK_0: Final = 0x18
        RESTART_TRIG_MASK_1: Final = 0x1C
        PAUSE_TRIG_MASK_0: Final   = 0x20
        PAUSE_TRIG_MASK_1: Final   = 0x24
        RESUME_TRIG_MASK_0: Final  = 0x28
        RESUME_TRIG_MASK_1: Final  = 0x2C

    class Bit(object):
        CTRL_RESET: Final     = 0
        CTRL_START: Final     = 1
        CTRL_TERMINATE: Final = 2
        CTRL_DONE_CLR: Final  = 3
        CTRL_PAUSE: Final     = 4
        CTRL_RESUME: Final    = 5
        CTRL_RESTART: Final   = 6
        DOUT_0: Final  = 0
        DOUT_1: Final  = 1
        DOUT_2: Final  = 2
        DOUT_3: Final  = 3
        DOUT_4: Final  = 4
        DOUT_5: Final  = 5
        DOUT_6: Final  = 6
        DOUT_7: Final  = 7
        DOUT_8: Final  = 8
        DOUT_9: Final  = 9
        DOUT_10: Final = 10
        DOUT_11: Final = 11
        DOUT_12: Final = 12
        DOUT_13: Final = 13
        DOUT_14: Final = 14
        DOUT_15: Final = 15
        DOUT_16: Final = 16
        DOUT_17: Final = 17
        DOUT_18: Final = 18
        DOUT_19: Final = 19
        DOUT_20: Final = 20
        DOUT_21: Final = 21
        DOUT_22: Final = 22
        DOUT_23: Final = 23
        DOUT_24: Final = 24
        DOUT_25: Final = 25
        DOUT_26: Final = 26
        DOUT_27: Final = 27
        DOUT_28: Final = 28
        DOUT_29: Final = 29
        DOUT_30: Final = 30
        DOUT_31: Final = 31
        DOUT_32: Final = 0
        DOUT_33: Final = 1

        __douts: Final = [
            DOUT_0,  DOUT_1,  DOUT_2,  DOUT_3,
            DOUT_4,  DOUT_5,  DOUT_6,  DOUT_7,
            DOUT_8,  DOUT_9,  DOUT_10, DOUT_11,
            DOUT_12, DOUT_13, DOUT_14, DOUT_15,
            DOUT_16, DOUT_17, DOUT_18, DOUT_19,
            DOUT_20, DOUT_21, DOUT_22, DOUT_23,
            DOUT_24, DOUT_25, DOUT_26, DOUT_27,
            DOUT_28, DOUT_29, DOUT_30, DOUT_31,
            DOUT_32, DOUT_33]

        @classmethod
        def dout(cls, idx: int) -> int:
            return cls.__douts[idx]


class DigitalOutCtrlRegs(object):

    class Addr(object):
        DOUT_0: Final  = 0x0080
        DOUT_1: Final  = 0x0100
        DOUT_2: Final  = 0x0180
        DOUT_3: Final  = 0x0200
        DOUT_4: Final  = 0x0280
        DOUT_5: Final  = 0x0300
        DOUT_6: Final  = 0x0380
        DOUT_7: Final  = 0x0400
        DOUT_8: Final  = 0x0480
        DOUT_9: Final  = 0x0500
        DOUT_10: Final = 0x0580
        DOUT_11: Final = 0x0600
        DOUT_12: Final = 0x0680
        DOUT_13: Final = 0x0700
        DOUT_14: Final = 0x0780
        DOUT_15: Final = 0x0800
        DOUT_16: Final = 0x0880
        DOUT_17: Final = 0x0900
        DOUT_18: Final = 0x0980
        DOUT_19: Final = 0x0A00
        DOUT_20: Final = 0x0A80
        DOUT_21: Final = 0x0B00
        DOUT_22: Final = 0x0B80
        DOUT_23: Final = 0x0C00
        DOUT_24: Final = 0x0C80
        DOUT_25: Final = 0x0D00
        DOUT_26: Final = 0x0D80
        DOUT_27: Final = 0x0E00
        DOUT_28: Final = 0x0E80
        DOUT_29: Final = 0x0F00
        DOUT_30: Final = 0x0F80
        DOUT_31: Final = 0x1000
        DOUT_32: Final = 0x1080
        DOUT_33: Final = 0x1100

        __douts: Final = [
            DOUT_0,  DOUT_1,  DOUT_2,  DOUT_3,
            DOUT_4,  DOUT_5,  DOUT_6,  DOUT_7,
            DOUT_8,  DOUT_9,  DOUT_10, DOUT_11,
            DOUT_12, DOUT_13, DOUT_14, DOUT_15,
            DOUT_16, DOUT_17, DOUT_18, DOUT_19,
            DOUT_20, DOUT_21, DOUT_22, DOUT_23,
            DOUT_24, DOUT_25, DOUT_26, DOUT_27,
            DOUT_28, DOUT_29, DOUT_30, DOUT_31,
            DOUT_32, DOUT_33]

        @classmethod
        def dout(cls, idx: int) -> int:
            return cls.__douts[idx]

    class Offset(object):
        CTRL: Final         = 0x0
        STATUS: Final       = 0x4
        NUM_PATTERNS: Final = 0x8
        START_IDX: Final    = 0xC

    class Bit(object):
        CTRL_RESET: Final     = 0
        CTRL_START: Final     = 1
        CTRL_TERMINATE: Final = 2
        CTRL_DONE_CLR: Final  = 3
        CTRL_PAUSE: Final     = 4
        CTRL_RESUME: Final    = 5
        CTRL_RESTART: Final   = 6
        STATUS_WAKEUP: Final  = 0
        STATUS_BUSY: Final    = 1
        STATUS_DONE: Final    = 2
        STATUS_PAUSED: Final  = 3


class DigitalOutputDataListRegs(object):
    #### digital output data params ####
    class Addr(object):
        DOUT_0: Final  = 0x10_0000
        DOUT_1: Final  = 0x14_0000
        DOUT_2: Final  = 0x18_0000
        DOUT_3: Final  = 0x1C_0000
        DOUT_4: Final  = 0x20_0000
        DOUT_5: Final  = 0x24_0000
        DOUT_6: Final  = 0x28_0000
        DOUT_7: Final  = 0x2C_0000
        DOUT_8: Final  = 0x30_0000
        DOUT_9: Final  = 0x34_0000
        DOUT_10: Final = 0x38_0000
        DOUT_11: Final = 0x3C_0000
        DOUT_12: Final = 0x40_0000
        DOUT_13: Final = 0x44_0000
        DOUT_14: Final = 0x48_0000
        DOUT_15: Final = 0x4C_0000
        DOUT_16: Final = 0x50_0000
        DOUT_17: Final = 0x54_0000
        DOUT_18: Final = 0x58_0000
        DOUT_19: Final = 0x5C_0000
        DOUT_20: Final = 0x60_0000
        DOUT_21: Final = 0x64_0000
        DOUT_22: Final = 0x68_0000
        DOUT_23: Final = 0x6C_0000
        DOUT_24: Final = 0x70_0000
        DOUT_25: Final = 0x74_0000
        DOUT_26: Final = 0x78_0000
        DOUT_27: Final = 0x7C_0000
        DOUT_28: Final = 0x80_0000
        DOUT_29: Final = 0x84_0000
        DOUT_30: Final = 0x88_0000
        DOUT_31: Final = 0x8C_0000
        DOUT_32: Final = 0x90_0000
        DOUT_33: Final = 0x94_0000

        __douts: Final = [
            DOUT_0,  DOUT_1,  DOUT_2,  DOUT_3,
            DOUT_4,  DOUT_5,  DOUT_6,  DOUT_7,
            DOUT_8,  DOUT_9,  DOUT_10, DOUT_11,
            DOUT_12, DOUT_13, DOUT_14, DOUT_15,
            DOUT_16, DOUT_17, DOUT_18, DOUT_19,
            DOUT_20, DOUT_21, DOUT_22, DOUT_23,
            DOUT_24, DOUT_25, DOUT_26, DOUT_27,
            DOUT_28, DOUT_29, DOUT_30, DOUT_31,
            DOUT_32, DOUT_33]

        @classmethod
        def dout(cls, idx: int) -> int:
            return cls.__douts[idx]

    class Offset(object):        
        @classmethod
        def pattern(cls, idx: int) -> int:
            return idx * 8

        BIT_PATTERN: Final = 0x0
        OUTPUT_TIME: Final = 0x4
        DEFAULT_BIT_PATTERN: Final = 0x1000
