import sys
from capturetestdsp import *
import random
import argparse

def main(num_tests, ip_addr, capture_modules, use_labrad, server_ip_addr):
    random.seed(10)

    failed_tests = []
    for test_id in range(num_tests):
        print("---- test {:03d} / {:03d} ----".format(test_id, num_tests - 1))
        res_dir = 'result/{:03d}'.format(test_id)
        test = CaptureTestDsp(res_dir, ip_addr, capture_modules, use_labrad, server_ip_addr)

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

        print('\n-- classification --')
        result = test.run_test('classification', DspUnit.CLASSIFICATION)
        if not result:
            print('failure classification')
            failed_tests.append('{} - classification'.format(test_id))

        print('\n-- all in integration path --')
        result = test.run_test(
            'integration_path',
            DspUnit.COMPLEX_FIR,
            DspUnit.DECIMATION,
            DspUnit.REAL_FIR,
            DspUnit.COMPLEX_WINDOW,
            DspUnit.SUM,
            DspUnit.INTEGRATION)
        if not result:
            print('failure all')
            failed_tests.append('{} - all in integration path'.format(test_id))

        print('\n-- all in classification path --')
        result = test.run_test(
            'classification_path',
            DspUnit.COMPLEX_FIR,
            DspUnit.DECIMATION,
            DspUnit.REAL_FIR,
            DspUnit.COMPLEX_WINDOW,
            DspUnit.SUM,
            DspUnit.CLASSIFICATION)
        if not result:
            print('failure all')
            failed_tests.append('{} - all in classification path'.format(test_id))
            
        print()

    if failed_tests:
        for test_id in failed_tests:
            print("Test {} failed.".format(test_id))
    else:
        print("All tests succeeded.".format(failed_tests))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--num-tests')
    parser.add_argument('--ipaddr')
    parser.add_argument('--capture-module')
    parser.add_argument('--server-ipaddr')
    parser.add_argument('--labrad', action='store_true')
    args = parser.parse_args()

    num_tests = 1
    if args.num_tests is not None:
        num_tests = int(args.num_tests)

    ip_addr = '10.0.0.16'
    if args.ipaddr is not None:
        ip_addr = args.ipaddr

    capture_modules = CaptureModule.all()
    if args.capture_module is not None:
        capture_modules = [CaptureModule.of(int(args.capture_module))]

    server_ip_addr = 'localhost'
    if args.server_ipaddr is not None:
        server_ip_addr = args.server_ipaddr

    main(
        num_tests,
        ip_addr,
        capture_modules,
        args.labrad,
        server_ip_addr)
