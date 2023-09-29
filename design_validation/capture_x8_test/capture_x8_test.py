import argparse
import sys
from capturetest import CaptureTest
from e7awgsw import CaptureModule


def main(num_tests, ip_addr, capture_modules, use_labrad, server_ip_addr, res_root_dir):

    failed_tests = []
    for test_id in range(num_tests):
        print("---- test {:03d} / {:03d} ----".format(test_id, num_tests - 1))
        res_dir = '{}/{:03d}'.format(res_root_dir, test_id)
        result = CaptureTest(
            res_dir, ip_addr, capture_modules, use_labrad, server_ip_addr).run_test()
        if not result:
            print('failure')
            failed_tests.append(test_id)

    if failed_tests:
        for test_id in failed_tests:
            print("Test {:03d} failed.".format(test_id))
        return 1
    else:
        print("All tests succeeded.".format(failed_tests))
        return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--num-tests', default=5, type=int)
    parser.add_argument('--ipaddr', default='10.1.0.255')
    parser.add_argument('--capture-module')
    parser.add_argument('--server-ipaddr', default='localhost')
    parser.add_argument('--labrad', action='store_true')
    parser.add_argument('--result-dir', default='result')
    args = parser.parse_args()

    capture_modules = CaptureModule.all()
    if args.capture_module is not None:
        capture_modules = [CaptureModule.of(int(args.capture_module))]

    status = main(
        args.num_tests,
        args.ipaddr,
        capture_modules,
        args.labrad,
        args.server_ipaddr,
        args.result_dir)

    sys.exit(status)
