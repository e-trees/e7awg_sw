from typing import Final

class AwgMasterCtrlRegs(object):
    ADDR: Final = 0x0

    class Offset(object):
        VERSION: Final             = 0x0
        CTRL_TARGET_SEL: Final     = 0x4
        CTRL: Final                = 0x8
        WAKEUP_STATUS: Final       = 0xC
        BUSY_STATUS: Final         = 0x10
        READY_STATUS: Final        = 0x14
        DONE_STATUS: Final         = 0x18
        READ_ERR: Final            = 0x1C
        SAMPLE_SHORTAGE_ERR: Final = 0x20
        PAUSED_STATUS: Final       = 0x24

    class Bit(object):
        CTRL_RESET: Final     = 0
        CTRL_PREPARE: Final   = 1
        CTRL_START: Final     = 2
        CTRL_TERMINATE: Final = 3
        CTRL_DONE_CLR: Final  = 4
        CTRL_PAUSE: Final     = 5
        CTRL_RESUME: Final    = 6

        AWG_0: Final  = 0
        AWG_1: Final  = 1
        AWG_2: Final  = 2
        AWG_3: Final  = 3
        AWG_4: Final  = 4
        AWG_5: Final  = 5
        AWG_6: Final  = 6
        AWG_7: Final  = 7
        AWG_8: Final  = 8
        AWG_9: Final  = 9
        AWG_10: Final = 10
        AWG_11: Final = 11
        AWG_12: Final = 12
        AWG_13: Final = 13
        AWG_14: Final = 14
        AWG_15: Final = 15

        __LIST: Final = [
            AWG_0,  AWG_1,  AWG_2,  AWG_3,
            AWG_4,  AWG_5,  AWG_6,  AWG_7,
            AWG_8,  AWG_9,  AWG_10, AWG_11,
            AWG_12, AWG_13, AWG_14, AWG_15]

        @classmethod
        def awg(cls, idx: int) -> int:
            return cls.__LIST[idx]


class AwgCtrlRegs(object):

    class Addr(object):
        AWG_0: Final  = 0x80
        AWG_1: Final  = 0x100
        AWG_2: Final  = 0x180
        AWG_3: Final  = 0x200
        AWG_4: Final  = 0x280
        AWG_5: Final  = 0x300
        AWG_6: Final  = 0x380
        AWG_7: Final  = 0x400
        AWG_8: Final  = 0x480
        AWG_9: Final  = 0x500
        AWG_10: Final = 0x580
        AWG_11: Final = 0x600
        AWG_12: Final = 0x680
        AWG_13: Final = 0x700
        AWG_14: Final = 0x780
        AWG_15: Final = 0x800
    
        __LIST: Final = [
            AWG_0,  AWG_1,  AWG_2,  AWG_3,
            AWG_4,  AWG_5,  AWG_6,  AWG_7,
            AWG_8,  AWG_9,  AWG_10, AWG_11,
            AWG_12, AWG_13, AWG_14, AWG_15]
    
        @classmethod
        def awg(cls, idx: int) -> int:
            return cls.__LIST[idx]

    class Offset(object):
        CTRL: Final   = 0x0
        STATUS: Final = 0x4
        ERR: Final    = 0x8

    class Bit(object):
        CTRL_RESET: Final          = 0
        CTRL_PREPARE: Final        = 1
        CTRL_START: Final          = 2
        CTRL_TERMINATE: Final      = 3
        CTRL_DONE_CLR: Final       = 4
        STATUS_WAKEUP: Final       = 0
        STATUS_BUSY: Final         = 1
        STATUS_READY: Final        = 2
        STATUS_DONE: Final         = 3
        ERR_READ: Final            = 0
        ERR_SAMPLE_SHORTAGE: Final = 1


class WaveParamRegs(object):
    #### wave params ####
    class Addr(object):
        AWG_0: Final  = 0x1000
        AWG_1: Final  = 0x1400
        AWG_2: Final  = 0x1800
        AWG_3: Final  = 0x1C00
        AWG_4: Final  = 0x2000
        AWG_5: Final  = 0x2400
        AWG_6: Final  = 0x2800
        AWG_7: Final  = 0x2C00
        AWG_8: Final  = 0x3000
        AWG_9: Final  = 0x3400
        AWG_10: Final = 0x3800
        AWG_11: Final = 0x3C00
        AWG_12: Final = 0x4000
        AWG_13: Final = 0x4400
        AWG_14: Final = 0x4800
        AWG_15: Final = 0x4C00

        __LIST: Final = [
            AWG_0,  AWG_1,  AWG_2,  AWG_3,
            AWG_4,  AWG_5,  AWG_6,  AWG_7,
            AWG_8,  AWG_9,  AWG_10, AWG_11,
            AWG_12, AWG_13, AWG_14, AWG_15]

        @classmethod
        def awg(cls, idx: int) -> int:
            return cls.__LIST[idx]

    class Offset(object):
        CHUNK_0: Final  = 0x40
        CHUNK_1: Final  = 0x50
        CHUNK_2: Final  = 0x60
        CHUNK_3: Final  = 0x70
        CHUNK_4: Final  = 0x80
        CHUNK_5: Final  = 0x90
        CHUNK_6: Final  = 0xA0
        CHUNK_7: Final  = 0xB0
        CHUNK_8: Final  = 0xC0
        CHUNK_9: Final  = 0xD0
        CHUNK_10: Final = 0xE0
        CHUNK_11: Final = 0xF0
        CHUNK_12: Final = 0x100
        CHUNK_13: Final = 0x110
        CHUNK_14: Final = 0x120
        CHUNK_15: Final = 0x130
        
        __LIST: Final = [
            CHUNK_0,  CHUNK_1,  CHUNK_2,  CHUNK_3,
            CHUNK_4,  CHUNK_5,  CHUNK_6,  CHUNK_7,
            CHUNK_8,  CHUNK_9,  CHUNK_10, CHUNK_11,
            CHUNK_12, CHUNK_13, CHUNK_14, CHUNK_15]
        
        @classmethod
        def chunk(cls, idx: int) -> int:
            return cls.__LIST[idx]

        NUM_WAIT_WORDS: Final                = 0x0
        NUM_REPEATS: Final                   = 0x4
        NUM_CHUNKS: Final                    = 0x8
        WAVE_STARTABLE_BLOCK_INTERVAL: Final = 0xC

        CHUNK_START_ADDR: Final    = 0x0
        NUM_WAVE_PART_WORDS: Final = 0x4
        NUM_BLANK_WORDS: Final     = 0x8
        NUM_CHUNK_REPEATS: Final   = 0xC


class CaptureMasterCtrlRegs(object):
    ADDR: Final = 0x0

    class Offset(object):
        VERSION: Final            = 0x0
        CAP_MOD_TRIG_SEL_0: Final = 0x4
        CAP_MOD_TRIG_SEL_1: Final = 0x8
        AWG_TRIG_MASK: Final      = 0xC
        CTRL_TARGET_SEL: Final    = 0x10
        CTRL: Final               = 0x14
        WAKEUP_STATUS: Final      = 0x18
        BUSY_STATUS: Final        = 0x1C
        DONE_STATUS: Final        = 0x20
        OVERFLOW_ERR: Final       = 0x24
        WRITE_ERR: Final          = 0x28
        CAP_MOD_TRIG_SEL_2: Final = 0x2C
        CAP_MOD_TRIG_SEL_3: Final = 0x30

    class Bit(object):
        CTRL_RESET: Final     = 0
        CTRL_START: Final     = 1
        CTRL_TERMINATE: Final = 2
        CTRL_DONE_CLR: Final  = 3
        CAPTURE_0: Final      = 0
        CAPTURE_1: Final      = 1
        CAPTURE_2: Final      = 2
        CAPTURE_3: Final      = 3
        CAPTURE_4: Final      = 4
        CAPTURE_5: Final      = 5
        CAPTURE_6: Final      = 6
        CAPTURE_7: Final      = 7
        CAPTURE_8: Final      = 8
        CAPTURE_9: Final      = 9
        
        __LIST: Final = [
            CAPTURE_0,  CAPTURE_1,  CAPTURE_2,  CAPTURE_3,
            CAPTURE_4,  CAPTURE_5,  CAPTURE_6,  CAPTURE_7,
            CAPTURE_8,  CAPTURE_9]
        
        @classmethod
        def capture(cls, idx: int) -> int:
            return cls.__LIST[idx]


class CaptureCtrlRegs(object):

    class Addr(object):
        CAPTURE_0: Final  = 0x100
        CAPTURE_1: Final  = 0x200
        CAPTURE_2: Final  = 0x300
        CAPTURE_3: Final  = 0x400
        CAPTURE_4: Final  = 0x500
        CAPTURE_5: Final  = 0x600
        CAPTURE_6: Final  = 0x700
        CAPTURE_7: Final  = 0x800
        CAPTURE_8: Final  = 0x900
        CAPTURE_9: Final  = 0xA00

        __LIST: Final = [
            CAPTURE_0, CAPTURE_1, CAPTURE_2, CAPTURE_3,
            CAPTURE_4, CAPTURE_5, CAPTURE_6, CAPTURE_7,
            CAPTURE_8, CAPTURE_9]
    
        @classmethod
        def capture(cls, idx: int) -> int:
            return cls.__LIST[idx]

    class Offset(object):
        CTRL: Final        = 0x0
        STATUS: Final      = 0x4
        ERR: Final         = 0x8
        CAP_MOD_SEL: Final = 0xC

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
        CAPTURE_0: Final  = 0x10000
        CAPTURE_1: Final  = 0x20000
        CAPTURE_2: Final  = 0x30000
        CAPTURE_3: Final  = 0x40000
        CAPTURE_4: Final  = 0x50000
        CAPTURE_5: Final  = 0x60000
        CAPTURE_6: Final  = 0x70000
        CAPTURE_7: Final  = 0x80000
        CAPTURE_8: Final  = 0x90000
        CAPTURE_9: Final  = 0xA0000

        __LIST: Final = [
            CAPTURE_0, CAPTURE_1, CAPTURE_2, CAPTURE_3,
            CAPTURE_4, CAPTURE_5, CAPTURE_6, CAPTURE_7,
            CAPTURE_8, CAPTURE_9]

        @classmethod
        def capture(cls, idx: int) -> int:
            return cls.__LIST[idx]

    class Offset(object):

        DSP_MODULE_ENABLE: Final    = 0x0
        CAPTURE_DELAY: Final        = 0x4
        CAPTURE_ADDR: Final         = 0x8
        NUM_CAPTURED_SAMPLES: Final = 0xC
        NUM_INTEG_SECTIONS: Final   = 0x10
        NUM_SUM_SECTIONS: Final     = 0x14
        SUM_START_TIME: Final       = 0x18
        SUM_END_TIME: Final         = 0x1C

        __MAX_SUM_SECTIONS: Final           = 4096
        __MAX_POST_BLANKS: Final            = 4096
        __MAX_COMP_FIR_REAL_COEFS: Final    = 16
        __MAX_COMP_FIR_IMAG_COEFS: Final    = 16
        __MAX_REAL_FIR_I_DATA_COEFS: Final  = 8
        __MAX_REAL_FIR_Q_DATA_COEFS: Final  = 8
        __MAX_COMP_WINDOW_REAL_COEFS: Final = 2048
        __MAX_COMP_WINDOW_IMGA_COEFS: Final = 2048
        __MAX_DECISION_FUNC_PARAMS: Final   = 6

        @classmethod
        def sum_section_length(cls, idx: int) -> int:
            if idx >= cls.__MAX_SUM_SECTIONS:
                raise ValueError("sum section length addr offset error")
            SUM_SEC_LEN_OFFSET = 0x1000
            return 4 * idx + SUM_SEC_LEN_OFFSET

        @classmethod
        def post_blank_length(cls, idx: int) -> int:
            if idx >= cls.__MAX_POST_BLANKS:
                raise ValueError("post blank length addr offset error")
            POST_BLANK_LEN_OFFSET = 0x5000
            return 4 * idx + POST_BLANK_LEN_OFFSET

        @classmethod
        def comp_fir_re_coef(cls, idx: int) -> int:
            if idx >= cls.__MAX_COMP_FIR_REAL_COEFS:
                raise ValueError("complex fir real coefficient addr offset error")
            COMP_FIR_REAL_COEF_OFFSET = 0x9000
            return 4 * idx + COMP_FIR_REAL_COEF_OFFSET

        @classmethod
        def comp_fir_im_coef(cls, idx: int) -> int:
            if idx >= cls.__MAX_COMP_FIR_IMAG_COEFS:
                raise ValueError("complex fir imaginary coefficient addr offset error")
            COMP_FIR_IMAGINARY_COEF_OFFSET = 0x9040
            return 4 * idx + COMP_FIR_IMAGINARY_COEF_OFFSET

        @classmethod
        def real_fir_i_coef(cls, idx: int) -> int:
            if idx >= cls.__MAX_REAL_FIR_I_DATA_COEFS:
                raise ValueError("real fir I data coefficient addr offset error")
            REAL_FIR_I_DATA_COEF_OFFSET = 0xA000
            return 4 * idx + REAL_FIR_I_DATA_COEF_OFFSET

        @classmethod
        def real_fir_q_coef(cls, idx: int) -> int:
            if idx >= cls.__MAX_REAL_FIR_Q_DATA_COEFS:
                raise ValueError("real fir Q data coefficient addr offset error")
            REAL_FIR_Q_DATA_COEF_OFFSET = 0xA020
            return 4 * idx + REAL_FIR_Q_DATA_COEF_OFFSET

        @classmethod
        def comp_window_re_coef(cls, idx: int) -> int:
            if idx >= cls.__MAX_COMP_WINDOW_REAL_COEFS:
                raise ValueError("complex window real coefficient addr offset error")
            COMP_WINDOW_REAL_COEF_OFFSET = 0xB000
            return 4 * idx + COMP_WINDOW_REAL_COEF_OFFSET

        @classmethod
        def comp_window_im_coef(cls, idx: int) -> int:
            if idx >= cls.__MAX_COMP_WINDOW_IMGA_COEFS:
                raise ValueError("complex window imaginary coefficient addr offset error")
            COMP_WINDOW_IMAGINARY_COEF_OFFSET = 0xD000
            return 4 * idx + COMP_WINDOW_IMAGINARY_COEF_OFFSET

        @classmethod
        def decision_func_params(cls, idx: int) -> int:
            if idx >= cls.__MAX_DECISION_FUNC_PARAMS:
                raise ValueError("decision func param addr offset error")
            DECISION_FUNC_PARAMS_OFFSET = 0xF000
            return 4 * idx + DECISION_FUNC_PARAMS_OFFSET
