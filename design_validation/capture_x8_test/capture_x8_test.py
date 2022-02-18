import argparse
from capturetest import *


def main(num_tests, capture_modules, use_labrad, server_ip_addr):

    failed_tests = []
    for test_id in range(num_tests):
        print("---- test {:03d} / {:03d} ----".format(test_id, num_tests - 1))
        res_dir = 'result/{:03d}'.format(test_id)
        result = CaptureTest(
            res_dir, capture_modules, use_labrad, server_ip_addr).run_test()
        if not result:
            print('failure')
            failed_tests.append(test_id)

    if failed_tests:
        for test_id in failed_tests:
            print("Test {:03d} failed.".format(test_id))
    else:
        print("All tests succeeded.".format(failed_tests))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--num-tests')
    parser.add_argument('--capture-module')
    parser.add_argument('--server-ipaddr')
    parser.add_argument('--labrad', action='store_true')
    args = parser.parse_args()

    num_tests = 10
    if args.num_tests is not None:
        num_tests = int(args.num_tests)

    capture_modules = CaptureModule.all()
    if args.capture_module is not None:
        capture_modules = [CaptureModule.of(int(args.capture_module))]

    server_ip_addr = 'localhost'
    if args.server_ipaddr is not None:
        server_ip_addr = args.server_ipaddr

    main(num_tests, capture_modules, args.labrad, server_ip_addr)
