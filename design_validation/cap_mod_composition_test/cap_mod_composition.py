import argparse
import sys
from capturetest import CaptureTest


def main(
    num_tests,
    ip_addr,
    use_labrad,
    server_ip_addr,
    num_cap_units_list,
    res_root_dir):

    failed_tests = []
    for test_id in range(num_tests):
        print("---- test {:03d} / {:03d} ----".format(test_id, num_tests - 1))
        res_dir = '{}/{:03d}'.format(res_root_dir, test_id)
        cap_test = CaptureTest(
            res_dir,
            ip_addr,
            use_labrad,
            server_ip_addr,
            num_cap_units_list)
        result = cap_test.run_test()
        if not result:
            print('failure')
            failed_tests.append(test_id)

    if failed_tests:
        for test_id in failed_tests:
            print("Test {:03d} failed.".format(test_id))
        return 1
    else:
        print('All tests succeeded.')
        return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--num-tests', default=1, type=int)
    parser.add_argument('--ipaddr', default='10.1.0.255')
    # テストする FPGA デザインでキャプチャモジュールに入っているキャプチャユニットの数
    parser.add_argument('--num-cap-units', default=[4, 4], nargs=2, type=int)
    parser.add_argument('--server-ipaddr', default='localhost')
    parser.add_argument('--labrad', action='store_true')
    parser.add_argument('--result-dir', default='result')
    args = parser.parse_args()

    status = main(
        args.num_tests,
        args.ipaddr,
        args.labrad,
        args.server_ipaddr,
        args.num_cap_units,
        args.result_dir)

    sys.exit(status)
