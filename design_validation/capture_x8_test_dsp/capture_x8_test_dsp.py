import sys
from capturetestdsp import *
import random

def main():

    try:
        num_tests = int(sys.argv[1])
    except Exception:
        num_tests = 1

    random.seed(10)

    failed_tests = []
    for test_id in range(num_tests):
        print("---- test {:03d} ----".format(test_id))
        res_dir = 'result/{:03d}'.format(test_id)
        test = CaptureTestDsp(res_dir)

        print('-- comp fir --')
        result = test.run_test('comp_fir', DspUnit.COMPLEX_FIR)
        if not result:
            print('failure comp fir')
            failed_tests.append('{} - comp_fir'.format(test_id))

        print('\n-- decimation --')
        result = test.run_test('decimation', DspUnit.DECIMATION)
        if not result:
            print('failure decimation')
            failed_tests.append('{} - decimation'.format(test_id))

        print('\n-- real fir --')
        result = test.run_test('real_fir', DspUnit.REAL_FIR)
        if not result:
            print('failure real fir')
            failed_tests.append('{} - real_fir'.format(test_id))

        print('\n-- window --')
        result = test.run_test('window', DspUnit.COMPLEX_WINDOW)
        if not result:
            print('failure window')
            failed_tests.append('{} - window'.format(test_id))

        print('\n-- sum --')
        result = test.run_test('sum', DspUnit.SUM)
        if not result:
            print('failure sum')
            failed_tests.append('{} - sum'.format(test_id))

        print('\n-- integration --')
        result = test.run_test('integ', DspUnit.INTEGRATION)
        if not result:
            print('failure integration')
            failed_tests.append('{} - integ'.format(test_id))

        print('\n-- all --')
        result = test.run_test('all', *DspUnit.all())
        if not result:
            print('failure all')
            failed_tests.append('{} - all'.format(test_id))
        print()

    if failed_tests:
        for test_id in failed_tests:
            print("Test {} failed.".format(test_id))
    else:
        print("All tests succeeded.".format(failed_tests))


if __name__ == "__main__":
    main()
