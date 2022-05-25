import argparse
from capturetest import *


def main(num_tests, ip_addr, use_labrad, server_ip_addr, res_root_dir):
    random.seed(10)

    failed_tests = []
    for test_id in range(num_tests):
        print("---- test {:03d} / {:03d} ----".format(test_id, num_tests - 1))

        res_dir = '{}/{:03d}/classification'.format(res_root_dir, test_id)
        result = CaptureTest(res_dir, ip_addr, use_labrad, server_ip_addr).run_test(True)
        if not result:
            print('failure classification\n')
            failed_tests.append('classification {}'.format(test_id))

        res_dir = '{}/{:03d}/no_dsp'.format(res_root_dir, test_id)
        result = CaptureTest(res_dir, ip_addr, use_labrad, server_ip_addr).run_test(False)
        if not result:
            print('failure no dsp\n')
            failed_tests.append('no dsp {}'.format(test_id))

    if failed_tests:
        for test_id in failed_tests:
            print("Test {:03d} failed.".format(test_id))
        return 1
    else:
        print("All tests succeeded.".format(failed_tests))
        return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--num-tests')
    parser.add_argument('--ipaddr')
    parser.add_argument('--server-ipaddr')
    parser.add_argument('--labrad', action='store_true')
    parser.add_argument('--result-dir')
    args = parser.parse_args()

    num_tests = 1
    if args.num_tests is not None:
        num_tests = int(args.num_tests)

    ip_addr = '10.0.0.16'
    if args.ipaddr is not None:
        ip_addr = args.ipaddr

    server_ip_addr = 'localhost'
    if args.server_ipaddr is not None:
        server_ip_addr = args.server_ipaddr

    res_root_dir = 'result'
    if args.result_dir is not None:
        res_root_dir = args.result_dir

    status = main(
        num_tests,
        ip_addr,
        args.labrad,
        server_ip_addr,
        res_root_dir)

    sys.exit(status)
