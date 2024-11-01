import random

def gen_consecutive_int_list(num_elems):
    return [(i + 1) for i in range(num_elems)]


def gen_random_int_list(num_elems, min, max):
    return [random.randint(min, max) for i in range(num_elems)]


def gen_zero_list(num_elems):
    return [0 for i in range(num_elems)]
