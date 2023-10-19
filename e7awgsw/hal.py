import logging
from abc import abstractmethod, ABCMeta
from typing import Any, List, Dict, Set, Tuple, cast
from pydantic import BaseModel, ValidationError

import numpy as np
import numpy.typing as npt

logger = logging.getLogger(__name__)


def p_1bf_bool(v: np.uint32, bidx: int) -> bool:
    return bool((v >> bidx) & 0x1)


def p_nbf(v: np.uint32, bidx0: int, bidx1: int) -> int:
    # Note: return type should be int rather than np.signedinteger for the accordance with pydantic
    return int((v >> bidx1) & ((1 << (bidx0 - bidx1 + 1)) - 1))


def b_1bf_bool(f: bool, bidx: int) -> np.uint32:
    return np.uint32(f << bidx)


def b_nbf(f: int, bidx0: int, bidx1: int) -> np.uint32:
    return np.uint32((f & ((1 << (bidx0 - bidx1 + 1)) - 1)) << bidx1)


class AbstractFpgaReg(BaseModel, validate_assignment=True, metaclass=ABCMeta):
    @abstractmethod
    def _parse(self, v: np.uint32) -> None:
        pass

    @abstractmethod
    def build(self) -> np.uint32:
        pass

    @classmethod
    def num_bytes(cls) -> int:
        return 4

    def __int__(self) -> np.uint32:
        return self.build()


class AbstractFpgaBitArrayReg(AbstractFpgaReg, metaclass=ABCMeta):
    @abstractmethod
    def __getitem__(self, k: int) -> bool:
        pass

    @abstractmethod
    def __setitem__(self, k: int, v: bool) -> None:
        pass


class AbstractFpgaRegfile(BaseModel, validate_assignment=True, metaclass=ABCMeta):
    def _parse_generic(self, v: npt.NDArray[Any]) -> None:
        for i, k in enumerate(self.model_fields):
            t: Any = self.model_fields[k].annotation
            if t is int:
                try:
                    setattr(self, k, v[i])
                except ValidationError:
                    logger.warning(f"invalid memory content 0x{v[i]:08x} for '{k}' is just ignored")
            elif hasattr(t, "parse"):
                try:
                    setattr(self, k, t.parse(v[i]))
                except ValidationError:
                    logger.warning(f"invalid memory content 0x{v[i]:08x} for '{k}' is just ignored")
            else:
                raise TypeError("invalid definition of RegFile")

    def _build_generic(self, dtype: str) -> npt.NDArray[Any]:
        ks = self.model_fields.keys()
        r = np.zeros(len(ks), dtype=dtype)
        for i, k in enumerate(ks):
            r[i] = getattr(self, k)
        return r

    @classmethod
    def num_bytes(cls):
        s = 0
        for k, v in cls.model_fields.items():
            a: Any = v.annotation
            m: List[Any] = v.metadata
            if a == int:
                s += 4
            elif hasattr(a, "num_bytes"):
                s += a.num_bytes()
            elif hasattr(a, "__origin__") and a.__origin__ == list and m[0].min_length == m[0].max_length:
                if a.__args__[0] == int:
                    s += 4 * v.metadata[0].min_length
                elif hasattr(a.__args__[0], "num_bytes"):
                    s += a.__args__[0].num_bytes() * v.metadata[0].min_length
                else:
                    raise AssertionError("invalid definition of data structure")
            else:
                raise AssertionError("invalid definition of data structure")
        return s

    @classmethod
    def num_words(cls):
        return cls.num_bytes() // 4


class AbstractFpgaRegfileU32(AbstractFpgaRegfile, metaclass=ABCMeta):
    def _parse(self, v: npt.NDArray[np.uint32]) -> None:
        self._parse_generic(v)

    def build(self) -> npt.NDArray[np.uint32]:
        return cast(npt.NDArray[np.uint32], self._build_generic("<u4"))


class AbstractFpgaRegfileI32(AbstractFpgaRegfile, metaclass=ABCMeta):
    def _parse(self, v: npt.NDArray[np.int32]) -> None:
        self._parse_generic(v)

    def build(self) -> npt.NDArray[np.int32]:
        return cast(npt.NDArray[np.int32], self._build_generic("<i4"))


class AbstractFpgaIO(metaclass=ABCMeta):
    @abstractmethod
    def write(self, addr: int, data: memoryview) -> None:
        pass

    @abstractmethod
    def write_u32(self, addr: int, data: np.uint32) -> None:
        pass

    @abstractmethod
    def write_i32(self, addr: int, data: np.int32) -> None:
        pass

    @abstractmethod
    def write_u32_vector(self, addr: int, data: npt.NDArray[np.uint32]) -> None:
        pass

    @abstractmethod
    def write_i32_vector(self, addr: int, data: npt.NDArray[np.int32]) -> None:
        pass

    @abstractmethod
    def read(self, addr: int, size: int) -> bytearray:
        pass

    @abstractmethod
    def read_u32(self, addr: int) -> np.uint32:
        pass

    @abstractmethod
    def read_i32(self, addr: int) -> np.int32:
        pass

    @abstractmethod
    def read_u32_vector(self, addr: int, num_elems: int) -> npt.NDArray[np.uint32]:
        pass

    @abstractmethod
    def read_i32_vector(self, addr: int, num_elems: int) -> npt.NDArray[np.int32]:
        pass


class AbstractFpgaProxy(metaclass=ABCMeta):
    REG_DECL: Dict[str, Tuple[int, type]] = {}

    def __init__(self, base: int, udprw: AbstractFpgaIO):
        self._base = base
        self._udprw: AbstractFpgaIO = udprw

    def get(self, regname: str) -> AbstractFpgaReg:
        return self._get(*self.REG_DECL[regname])

    def _get(self, offset: int, reg_type: type) -> AbstractFpgaReg:
        v = self._udprw.read_u32(self._base + offset)
        r = reg_type()
        try:
            r.parse(v)
        except ValidationError:
            logger.warning(f"invalid memory content 0x{v:08x} at {self._base + offset} is just ignored")
        return r

    def set(self, regname: str, v: AbstractFpgaReg):
        self._set(*self.REG_DECL[regname], v=v)

    def _set(self, offset:int, reg_type: type, v: AbstractFpgaReg):
        if not isinstance(v, reg_type):
            raise TypeError(f"invalid object for AwgMasterCtrlRegs[{offset}]")
        self._udprw.write_u32(self._base + offset, v.build())

    def update(self, regname: str, **fields):
        self._update(*self.REG_DECL[regname], **fields)

    def _update(self, offset: int, reg_type: type, **fields):
        r = self._get(offset, reg_type)
        for k, v in fields.items():
            setattr(r, k, v)
        self._set(offset, reg_type, r)

    def update_bit(self, regname: str, index: int, value: bool):
        self._update_bit(*self.REG_DECL[regname], index=index, value=value)

    def _update_bit(self, offset: int, reg_type: type, index: int, value: bool):
        r = self._get(offset, reg_type)
        if isinstance(r, AbstractFpgaBitArrayReg):
            r[index] = value
            self._set(offset, reg_type, r)
        else:
            raise ValueError("no array access is supported")

    def update_bits(self, regname: str, bits_to_clr: Set[int], bits_to_set: Set[int]):
        if len(bits_to_clr.intersection(bits_to_set)) != 0:
            raise ValueError("some bits are set and cleared at the same time.")
        self._update_bits(*self.REG_DECL[regname], bits_to_clr=bits_to_clr, bits_to_set=bits_to_set)

    def _update_bits(self, offset: int, reg_type: type, bits_to_clr: Set[int], bits_to_set: Set[int]):
        r = self._get(offset, reg_type)
        if isinstance(r, AbstractFpgaBitArrayReg):
            for b in bits_to_clr:
                r[b] = False
            for b in bits_to_set:
                r[b] = True
            self._set(offset, reg_type, r)
        else:
            raise ValueError("no array access is supported")
