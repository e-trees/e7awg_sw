import argparse
import random
import sys
import pathlib
from capturetest import CaptureTest

lib_path = str(pathlib.Path(__file__).resolve().parents[2])
sys.path.append(lib_path)
from e7awgsw import CaptureUnit


def main(num_tests, ip_addr, use_labrad, server_ip_addr, res_root_dir, cap_unit_id):
    random.seed(10)

    failed_tests = []
    for test_id in range(num_tests):
        print("---- test {:03d} / {:03d} ----".format(test_id, num_tests - 1))

        if (cap_unit_id != CaptureUnit.U8) and (cap_unit_id != CaptureUnit.U9):
            res_dir = '{}/cap_{}/{:03d}/classification'.format(res_root_dir, cap_unit_id, test_id)
            test = CaptureTest(res_dir, ip_addr, cap_unit_id, use_labrad, server_ip_addr)
            result = test.run_test(True)
            if not result:
                print('failure classification\n')
                failed_tests.append('classification {}'.format(test_id))

        res_dir = '{}/cap_{}/{:03d}/no_dsp'.format(res_root_dir, cap_unit_id, test_id)
        test = CaptureTest(res_dir, ip_addr, cap_unit_id, use_labrad, server_ip_addr)
        result = test.run_test(False)
        if not result:
            print('failure no dsp\n')
            failed_tests.append('no dsp {}'.format(test_id))

    if failed_tests:
        for test_id in failed_tests:
            print("Test {} failed.".format(test_id))
        return 1
    else:
        print("All tests succeeded.".format(failed_tests))
        return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--num-tests', default=1, type=int)
    parser.add_argument('--ipaddr', default='10.1.0.255')
    parser.add_argument('--server-ipaddr', default='localhost')
    parser.add_argument('--labrad', action='store_true')
    parser.add_argument('--result-dir', default='result')
    parser.add_argument('--capture-unit')
    args = parser.parse_args()

    cap_unit_id = CaptureUnit.U3
    if args.capture_unit is not None:
        cap_unit_id = CaptureUnit.of(int(args.capture_unit))

    status = main(
        args.num_tests,
        args.ipaddr,
        args.labrad,
        args.server_ipaddr,
        args.result_dir,
        cap_unit_id)

    sys.exit(status)
