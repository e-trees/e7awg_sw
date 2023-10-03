from enum import IntEnum, Enum

class CaptureUnit(IntEnum):
    """キャプチャユニットの ID"""
    U0 = 0
    U1 = 1
    U2 = 2
    U3 = 3
    U4 = 4
    U5 = 5
    U6 = 6
    U7 = 7

    @classmethod
    def all(cls):
        """全キャプチャユニットの ID をリストとして返す"""
        return [item for item in CaptureUnit]

    @classmethod
    def of(cls, val):
        if not CaptureUnit.includes(val):
            raise ValueError("Cannot convert {} to CaptureUnit".format(val))
        return CaptureUnit.all()[val]

    @classmethod
    def includes(cls, *vals):
        units = cls.all()
        return all([val in units for val in vals])


class CaptureModule(IntEnum):
    """キャプチャモジュール (複数のキャプチャユニットをまとめて保持するモジュール) の列挙型"""
    U0 = 0
    U1 = 1

    @classmethod
    def all(cls):
        """全キャプチャモジュールの ID をリストとして返す"""
        return [item for item in CaptureModule]

    @classmethod
    def of(cls, val):
        if not CaptureModule.includes(val):
            raise ValueError("Cannot convert {} to CaptureModule".format(val))
        return CaptureModule.all()[val]

    @classmethod
    def includes(cls, *vals):
        mods = cls.all()
        return all([val in mods for val in vals])

    @classmethod
    def get_units(cls, *capmod_id_list):
        """引数で指定したキャプチャモジュールが保持するキャプチャユニットの ID を取得する

        Args:
            *capmod_id_list (list of CaptureModule): キャプチャユニットを取得するキャプチャモジュール ID
        
        Returns:
            list of CaptureUnit: capmod_id_list に対応するキャプチャモジュールが保持するキャプチャユニットのリスト
        """
        units = []
        for capmod_id in set(capmod_id_list):
            if capmod_id == cls.U0:
                units += [CaptureUnit.U0, CaptureUnit.U1, CaptureUnit.U2, CaptureUnit.U3]
            elif capmod_id == cls.U1:
                units += [CaptureUnit.U4, CaptureUnit.U5, CaptureUnit.U6, CaptureUnit.U7]
            else:
                raise ValueError('Invalid capture module ID {}'.format(capmod_id))
        return sorted(units)


class AWG(IntEnum):
    """AWG の ID"""
    U0  = 0 
    U1  = 1 
    U2  = 2 
    U3  = 3 
    U4  = 4 
    U5  = 5 
    U6  = 6 
    U7  = 7 
    U8  = 8 
    U9  = 9 
    U10 = 10
    U11 = 11
    U12 = 12
    U13 = 13
    U14 = 14
    U15 = 15

    @classmethod
    def all(cls):
        """全 AWG の ID をリストとして返す"""
        return [item for item in AWG]

    @classmethod
    def of(cls, val):
        if not cls.includes(val):
            raise ValueError("connot convert {} to AWG".format(val))
        return cls.all()[val]

    @classmethod
    def includes(cls, *vals):
        awgs = cls.all()
        return all([val in awgs for val in vals])


class AwgErr(Enum):
    """AWG エラーの列挙型"""

    MEM_RD = 0
    SAMPLE_SHORTAGE = 1

    @classmethod
    def all(cls):
        """全 AWG エラーの列挙子をリストとして返す"""
        return [item for item in AwgErr]

    @classmethod
    def includes(cls, *vals):
        errs = cls.all()
        return all([val in errs for val in vals])


class CaptureErr(Enum):
    """キャプチャユニットエラーの列挙型"""

    MEM_WR = 0
    OVERFLOW = 1

    @classmethod
    def all(cls):
        """全キャプチャユニットエラーの列挙子をリストとして返す"""
        return [item for item in CaptureErr]

    @classmethod
    def includes(cls, *vals):
        errs = cls.all()
        return all([val in errs for val in vals])
