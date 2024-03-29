from __future__ import annotations

from typing import Any, TypeVar, overload
from typing_extensions import Self
from collections.abc import Sequence, Iterator

class ClassificationResult(Sequence[int]):
    """四値化結果を保持するクラス"""

    def __init__(self, result: bytes, num_results: int) -> None:
        self.__result = bytes(result)
        self.__len = num_results


    def __repr__(self) -> str:
        return self.__str__()


    def __str__(self) -> str:
        len = min(self.__len, 12)
        items = []
        for i in range(len):
            items.append(str(self[i]))
        if self.__len > 12:
            items.append('...')
        return '[' + ', '.join(items) + ']'


    def __iter__(self) -> Iterator[int]:
        return self.Iter(self)

    
    @overload
    def __getitem__(self, index: int) -> int: ...


    @overload
    def __getitem__(self, index: slice) -> Sequence[int]: ...


    def __getitem__(self, key: int | slice) -> int | Sequence[int]:
        if isinstance(key, int):
            return self.get(key)
        elif isinstance(key, slice):
            num_results = 0
            count = 0
            bits = [0,0,0,0]
            new_result = bytearray()
            for i in range(*key.indices(self.__len)):
                bits[count] = self.get(i)
                num_results += 1
                count += 1
                if count % 4 == 0:
                    new_result.append((bits[3] << 6) | (bits[2] << 4) | (bits[1] << 2) | bits[0])
                    count = 0

            if count != 0:
                new_result.append((bits[3] << 6) | (bits[2] << 4) | (bits[1] << 2) | bits[0])

            return ClassificationResult(new_result, num_results)
        else:
            raise TypeError('Invalid argument type.')

    
    def get(self, key: int) -> int:
        if key < 0:
            key += self.__len
        if (key < 0) or (self.__len <= key):
            raise IndexError('The index [{}] is out of range.'.format(key))
        i = key // 4
        j = key % 4
        return 0x3 & (self.__result[i] >> (j * 2))


    def __len__(self) -> int:
        return self.__len


    def __contains__(self, item: object) -> bool:
        for i in range(self.__len):
            if self[i] == item:
                return True

        return False


    def __eq__(self, other: Any) -> bool:
        try:
            if self is other:
                return True
                        
            if (other is None) or (len(self) != len(other)):
                return False

            for i in range(len(self)):
                if self[i] != other[i]:
                    return False

            return True
        except:
            return NotImplemented


    def __ne__(self, other: object) -> bool:
        return not self == other


    class Iter(Iterator[int]):

        def __init__(self, outer: ClassificationResult):
            self._i = 0
            self.__outer = outer


        def __iter__(self) -> Self:
            return self

            
        def __next__(self) -> int:
            if self._i == len(self.__outer):
                raise StopIteration()
            val = self.__outer.get(self._i)
            self._i += 1
            return val
