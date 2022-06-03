import sys
import pathlib


class RwRegister:
    """読み書き可能なレジスタ"""
    
    def __init__(self, num_bits, val):
        self.__num_bits = num_bits
        self.__val = self.__to_unsigned(val)
        self.__bits_and_action_list = []


    def add_on_change(self, action, *bit_indices):
        """レジスタの値が変わった時のイベントハンドラを登録する
        
        | イベントハンドラは登録した順に呼び出される.
        """
        self.__bits_and_action_list.append((bit_indices, action))


    def set(self, val):
        old = self.__val
        self.__val = self.__to_unsigned(val)
        for bit_indices, action in self.__bits_and_action_list:
            old_bits = self.__gen_bit_set(old, *bit_indices)
            new_bits = self.__gen_bit_set(self.__val, *bit_indices)
            if old_bits != new_bits:
                action(old_bits, new_bits)


    def get(self):
        return self.__val


    def get_bit(self, idx):
        return (self.get() >> idx) & 1


    def __gen_bit_set(self, val, *bit_indices):
        bits = []
        for bit_idx in bit_indices:
            bits.append((val >> bit_idx) & 1)
        return bits


    def __to_unsigned(self, val):
        return val & ((1 << self.__num_bits) - 1)


class RoRegister:
    """読み出し専用レジスタ"""

    def __init__(self, num_bits, val = 0):
        self.__num_bits = num_bits
        self.__bits_and_action_list = []
        self.__val = self.__to_unsigned(val)


    def add_on_read(self, action, *bit_indices):
        """レジスタ読み出し時のイベントハンドラを登録する
            
        | イベントハンドラは登録した順に呼び出される.
        """
        self.__bits_and_action_list.append((bit_indices, action))


    def get(self):
        bit_vals = [(self.__val >> i) & 1 for i in range(self.__num_bits)]
        for bit_indices, action in self.__bits_and_action_list:
            vals = action()
            for i in range(len(vals)):
                bit_vals[bit_indices[i]] = vals[i]

        reg_val = 0
        for i in range(len(bit_vals)):
            reg_val |= bit_vals[i] << i
        
        return reg_val


    def get_bit(self, idx):
        return (self.get() >> idx) & 1

    def __to_unsigned(self, val):
        return val & ((1 << self.__num_bits) - 1)
