
class ClassificationResult:
    """四値化結果を保持するクラス"""

    def __init__(self, result, num_results):
        self.__result = result
        self.__len = num_results


    def __repr__(self):
        return self.__str__()


    def __str__(self):
        len = min(self.__len, 12)
        items = []
        for i in range(len):
            items.append(str(self[i]))
        if self.__len > 12:
            items.append('...')
        return '[' + ', '.join(items) + ']'


    def __iter__(self):
        return self.Iter(self)


    def __getitem__(self, key):
        if isinstance(key, int):
            if key < 0:
                key += self.__len
            if (key < 0) or (self.__len <= key):
                raise IndexError('The index [{}] is out of range.'.format(key))
            i = key // 4
            j = key % 4
            return 0x3 & (self.__result[i] >> (j * 2))

        elif isinstance(key, slice):
            num_results = 0
            count = 0
            bits = [0,0,0,0]
            new_result = bytearray()
            for i in range(*key.indices(self.__len)):
                bits[count] = self[i]
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


    def __len__(self):
        return self.__len

    def __contains__(self, item):
        for i in range(self.__len):
            if self[i] == item:
                return True

        return False


    def __eq__(self, other):
        try:
            if len(other) != self.__len:
                return False

            for i in range(self.__len):
                if self[i] != other[i]:
                    return False

            return True
        except:
            cls_name = other.__class__.__name__
            raise NotImplementedError(
                'comparison between ClassificationResult and {} is not supported'.format(cls_name))


    def __ne__(self, other):
        return not self.__eq__(other)


    class Iter(object):

        def __init__(self, outer):
            self._i = 0
            self.__outer = outer

        def __next__(self):
            if self._i == len(self.__outer):
                raise StopIteration()
            val = self.__outer[self._i]
            self._i += 1
            return val
