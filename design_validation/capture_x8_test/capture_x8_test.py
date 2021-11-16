import sys
from capturetest import *
from qubelib import wavesequence

def main():
    try:
        num_tests = int(sys.argv[1])
    except Exception:
        num_tests = 10

    failed_tests = []
    for test_id in range(num_tests):
        print("---- test {:03d} ----".format(test_id))
        res_dir = 'result/{:03d}'.format(test_id)
        result = CaptureTest(res_dir).run_test()
        if not result:
            print('failure')
            failed_tests.append(test_id)

    if failed_tests:
        for test_id in failed_tests:
            print("Test {:03d} failed.".format(test_id))
    else:
        print("All tests succeeded.".format(failed_tests))

if __name__ == "__main__":
    main()
