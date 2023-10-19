
class AwgMasterCtrlRegs(object):
    ADDR = 0x0

    class Offset(object):
        VERSION             = 0x0
        CTRL_TARGET_SEL     = 0x4
        CTRL                = 0x8
        WAKEUP_STATUS       = 0xC
        BUSY_STATUS         = 0x10
        READY_STATUS        = 0x14
        DONE_STATUS         = 0x18
        READ_ERR            = 0x1C
        SAMPLE_SHORTAGE_ERR = 0x20

    class Bit(object):
        CTRL_RESET     = 0
        CTRL_PREPARE   = 1
        CTRL_START     = 2
        CTRL_TERMINATE = 3
        CTRL_DONE_CLR  = 4
        AWG_0  = 0
        AWG_1  = 1
        AWG_2  = 2
        AWG_3  = 3
        AWG_4  = 4
        AWG_5  = 5
        AWG_6  = 6
        AWG_7  = 7
        AWG_8  = 8
        AWG_9  = 9
        AWG_10 = 10
        AWG_11 = 11
        AWG_12 = 12
        AWG_13 = 13
        AWG_14 = 14
        AWG_15 = 15

        @classmethod
        def awg(cls, idx):
            awgs = [cls.AWG_0,  cls.AWG_1,  cls.AWG_2,  cls.AWG_3,
                    cls.AWG_4,  cls.AWG_5,  cls.AWG_6,  cls.AWG_7,
                    cls.AWG_8,  cls.AWG_9,  cls.AWG_10, cls.AWG_11,
                    cls.AWG_12, cls.AWG_13, cls.AWG_14, cls.AWG_15]
            return awgs[idx]


class AwgCtrlRegs(object):

    class Addr(object):
        AWG_0  = 0x80
        AWG_1  = 0x100
        AWG_2  = 0x180
        AWG_3  = 0x200
        AWG_4  = 0x280
        AWG_5  = 0x300
        AWG_6  = 0x380
        AWG_7  = 0x400
        AWG_8  = 0x480
        AWG_9  = 0x500
        AWG_10 = 0x580
        AWG_11 = 0x600
        AWG_12 = 0x680
        AWG_13 = 0x700
        AWG_14 = 0x780
        AWG_15 = 0x800
    
        @classmethod
        def awg(cls, idx):
            awgs = [cls.AWG_0,  cls.AWG_1,  cls.AWG_2,  cls.AWG_3,
                    cls.AWG_4,  cls.AWG_5,  cls.AWG_6,  cls.AWG_7,
                    cls.AWG_8,  cls.AWG_9,  cls.AWG_10, cls.AWG_11,
                    cls.AWG_12, cls.AWG_13, cls.AWG_14, cls.AWG_15]
            return awgs[idx]

    class Offset(object):
        CTRL   = 0x0
        STATUS = 0x4
        ERR    = 0x8

    class Bit(object):
        CTRL_RESET          = 0
        CTRL_PREPARE        = 1
        CTRL_START          = 2
        CTRL_TERMINATE      = 3
        CTRL_DONE_CLR       = 4
        STATUS_WAKEUP       = 0
        STATUS_BUSY         = 1
        STATUS_READY        = 2
        STATUS_DONE         = 3
        ERR_READ            = 0
        ERR_SAMPLE_SHORTAGE = 1


class WaveParamRegs(object):
    #### wave params ####
    class Addr(object):
        AWG_0  = 0x1000
        AWG_1  = 0x1400
        AWG_2  = 0x1800
        AWG_3  = 0x1C00
        AWG_4  = 0x2000
        AWG_5  = 0x2400
        AWG_6  = 0x2800
        AWG_7  = 0x2C00
        AWG_8  = 0x3000
        AWG_9  = 0x3400
        AWG_10 = 0x3800
        AWG_11 = 0x3C00
        AWG_12 = 0x4000
        AWG_13 = 0x4400
        AWG_14 = 0x4800
        AWG_15 = 0x4C00

        @classmethod
        def awg(cls, idx):
            awgs = [cls.AWG_0,  cls.AWG_1,  cls.AWG_2,  cls.AWG_3,
                    cls.AWG_4,  cls.AWG_5,  cls.AWG_6,  cls.AWG_7,
                    cls.AWG_8,  cls.AWG_9,  cls.AWG_10, cls.AWG_11,
                    cls.AWG_12, cls.AWG_13, cls.AWG_14, cls.AWG_15]
            return awgs[idx]

    class Offset(object):
        CHUNK_0  = 0x40
        CHUNK_1  = 0x50
        CHUNK_2  = 0x60
        CHUNK_3  = 0x70
        CHUNK_4  = 0x80
        CHUNK_5  = 0x90
        CHUNK_6  = 0xA0
        CHUNK_7  = 0xB0
        CHUNK_8  = 0xC0
        CHUNK_9  = 0xD0
        CHUNK_10 = 0xE0
        CHUNK_11 = 0xF0
        CHUNK_12 = 0x100
        CHUNK_13 = 0x110
        CHUNK_14 = 0x120
        CHUNK_15 = 0x130
        
        @classmethod
        def chunk(cls, idx):
            chunks = [cls.CHUNK_0,  cls.CHUNK_1,  cls.CHUNK_2,  cls.CHUNK_3,
                      cls.CHUNK_4,  cls.CHUNK_5,  cls.CHUNK_6,  cls.CHUNK_7,
                      cls.CHUNK_8,  cls.CHUNK_9,  cls.CHUNK_10, cls.CHUNK_11,
                      cls.CHUNK_12, cls.CHUNK_13, cls.CHUNK_14, cls.CHUNK_15]
            return chunks[idx]

        NUM_WAIT_WORDS                = 0x0
        NUM_REPEATS                   = 0x4
        NUM_CHUNKS                    = 0x8
        WAVE_STARTABLE_BLOCK_INTERVAL = 0xC

        CHUNK_START_ADDR    = 0x0
        NUM_WAVE_PART_WORDS = 0x4
        NUM_BLANK_WORDS     = 0x8
        NUM_CHUNK_REPEATS   = 0xC


class CaptureMasterCtrlRegs(object):
    ADDR = 0x0

    class Offset(object):
        VERSION         = 0x0
        TRIG_AWG_SEL_0  = 0x4
        TRIG_AWG_SEL_1  = 0x8
        AWG_TRIG_MASK   = 0xC
        CTRL_TARGET_SEL = 0x10
        CTRL            = 0x14
        WAKEUP_STATUS   = 0x18
        BUSY_STATUS     = 0x1C
        DONE_STATUS     = 0x20
        OVERFLOW_ERR    = 0x24
        WRITE_ERR       = 0x28

    class Bit(object):
        CTRL_RESET     = 0
        CTRL_START     = 1
        CTRL_TERMINATE = 2
        CTRL_DONE_CLR  = 3
        CAPTURE_0      = 0
        CAPTURE_1      = 1
        CAPTURE_2      = 2
        CAPTURE_3      = 3
        CAPTURE_4      = 4
        CAPTURE_5      = 5
        CAPTURE_6      = 6
        CAPTURE_7      = 7
        
        @classmethod
        def capture(cls, idx):
            capture_units = [
                cls.CAPTURE_0,  cls.CAPTURE_1,  cls.CAPTURE_2,  cls.CAPTURE_3,
                cls.CAPTURE_4,  cls.CAPTURE_5,  cls.CAPTURE_6,  cls.CAPTURE_7]
            return capture_units[idx]


class CaptureCtrlRegs(object):

    class Addr(object):
        CAPTURE_0  = 0x100
        CAPTURE_1  = 0x200
        CAPTURE_2  = 0x300
        CAPTURE_3  = 0x400
        CAPTURE_4  = 0x500
        CAPTURE_5  = 0x600
        CAPTURE_6  = 0x700
        CAPTURE_7  = 0x800
    
        @classmethod
        def capture(cls, idx):
            capture_units = [
                cls.CAPTURE_0, cls.CAPTURE_1, cls.CAPTURE_2, cls.CAPTURE_3,
                cls.CAPTURE_4, cls.CAPTURE_5, cls.CAPTURE_6, cls.CAPTURE_7]
            return capture_units[idx]

    class Offset(object):
        CTRL   = 0x0
        STATUS = 0x4
        ERR    = 0x8

    class Bit(object):
        CTRL_RESET     = 0
        CTRL_START     = 1
        CTRL_TERMINATE = 2
        CTRL_DONE_CLR  = 3
        STATUS_WAKEUP  = 0
        STATUS_BUSY    = 1
        STATUS_DONE    = 2
        ERR_OVERFLOW   = 0
        ERR_WRITE      = 1


class CaptureParamRegs(object):
    #### capture params ####
    class Addr(object):
        CAPTURE_0  = 0x10000
        CAPTURE_1  = 0x20000
        CAPTURE_2  = 0x30000
        CAPTURE_3  = 0x40000
        CAPTURE_4  = 0x50000
        CAPTURE_5  = 0x60000
        CAPTURE_6  = 0x70000
        CAPTURE_7  = 0x80000

        @classmethod
        def capture(cls, idx):
            capture_units = [
                cls.CAPTURE_0, cls.CAPTURE_1, cls.CAPTURE_2, cls.CAPTURE_3,
                cls.CAPTURE_4, cls.CAPTURE_5, cls.CAPTURE_6, cls.CAPTURE_7]
            return capture_units[idx]

    class Offset(object):

        DSP_MODULE_ENABLE    = 0x0
        CAPTURE_DELAY        = 0x4
        CAPTURE_ADDR         = 0x8
        NUM_CAPTURED_SAMPLES = 0xC
        NUM_INTEG_SECTIONS   = 0x10
        NUM_SUM_SECTIONS     = 0x14
        SUM_START_TIME       = 0x18
        SUM_END_TIME         = 0x1C

        __MAX_SUM_SECTIONS           = 4096
        __MAX_POST_BLANKS            = 4096
        __MAX_COMP_FIR_REAL_COEFS    = 16
        __MAX_COMP_FIR_IMAG_COEFS    = 16
        __MAX_REAL_FIR_I_DATA_COEFS  = 8
        __MAX_REAL_FIR_Q_DATA_COEFS  = 8
        __MAX_COMP_WINDOW_REAL_COEFS = 2048
        __MAX_COMP_WINDOW_IMGA_COEFS = 2048
        __MAX_DECISION_FUNC_PARAMS   = 6

        @classmethod
        def sum_section_length(cls, idx):
            if idx >= cls.__MAX_SUM_SECTIONS:
                raise ValueError("sum section length addr offset error")
            SUM_SEC_LEN_OFFSET = 0x1000
            return 4 * idx + SUM_SEC_LEN_OFFSET

        @classmethod
        def post_blank_length(cls, idx):
            if idx >= cls.__MAX_POST_BLANKS:
                raise ValueError("post blank length addr offset error")
            POST_BLANK_LEN_OFFSET = 0x5000
            return 4 * idx + POST_BLANK_LEN_OFFSET

        @classmethod
        def comp_fir_re_coef(cls, idx):
            if idx >= cls.__MAX_COMP_FIR_REAL_COEFS:
                raise ValueError("complex fir real coefficient addr offset error")
            COMP_FIR_REAL_COEF_OFFSET = 0x9000
            return 4 * idx + COMP_FIR_REAL_COEF_OFFSET

        @classmethod
        def comp_fir_im_coef(cls, idx):
            if idx >= cls.__MAX_COMP_FIR_IMAG_COEFS:
                raise ValueError("complex fir imaginary coefficient addr offset error")
            COMP_FIR_IMAGINARY_COEF_OFFSET = 0x9040
            return 4 * idx + COMP_FIR_IMAGINARY_COEF_OFFSET

        @classmethod
        def real_fir_i_coef(cls, idx):
            if idx >= cls.__MAX_REAL_FIR_I_DATA_COEFS:
                raise ValueError("real fir I data coefficient addr offset error")
            REAL_FIR_I_DATA_COEF_OFFSET = 0xA000
            return 4 * idx + REAL_FIR_I_DATA_COEF_OFFSET

        @classmethod
        def real_fir_q_coef(cls, idx):
            if idx >= cls.__MAX_REAL_FIR_Q_DATA_COEFS:
                raise ValueError("real fir Q data coefficient addr offset error")
            REAL_FIR_Q_DATA_COEF_OFFSET = 0xA020
            return 4 * idx + REAL_FIR_Q_DATA_COEF_OFFSET

        @classmethod
        def comp_window_re_coef(cls, idx):
            if idx >= cls.__MAX_COMP_WINDOW_REAL_COEFS:
                raise ValueError("complex window real coefficient addr offset error")
            COMP_WINDOW_REAL_COEF_OFFSET = 0xB000
            return 4 * idx + COMP_WINDOW_REAL_COEF_OFFSET

        @classmethod
        def comp_window_im_coef(cls, idx):
            if idx >= cls.__MAX_COMP_WINDOW_IMGA_COEFS:
                raise ValueError("complex window imaginary coefficient addr offset error")
            COMP_WINDOW_IMAGINARY_COEF_OFFSET = 0xD000
            return 4 * idx + COMP_WINDOW_IMAGINARY_COEF_OFFSET

        @classmethod
        def decision_func_params(cls, idx):
            if idx >= cls.__MAX_DECISION_FUNC_PARAMS:
                raise ValueError("decision func param addr offset error")
            DECISION_FUNC_PARAMS_OFFSET = 0xF000
            return 4 * idx + DECISION_FUNC_PARAMS_OFFSET
