import argparse
import pathlib
import sys
import random
from capturetestdsp import CaptureTestDsp

lib_path = str(pathlib.Path(__file__).resolve().parents[3])
sys.path.append(lib_path)
from e7awgsw import CaptureModule, DspUnit

def main(
    num_tests,
    ip_addr,
    capture_modules,
    use_labrad,
    server_ip_addr,
    only_all,
    skip_test,
    output_sim_data):
    random.seed(10)

    failed_tests = []
    for test_id in range(num_tests):
        print("---- test {:03d} / {:03d} ----".format(test_id, num_tests - 1))
        res_dir = 'result/{:03d}'.format(test_id)
        test = CaptureTestDsp(
            res_dir,
            ip_addr,
            capture_modules,
            use_labrad,
            server_ip_addr,
            skip_test,
            output_sim_data)
            
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
    parser = argparse.ArgumentParser()
    parser.add_argument('--num-tests', default=1, type=int)
    parser.add_argument('--ipaddr', default='10.1.0.255')
    parser.add_argument('--capture-module')
    parser.add_argument('--server-ipaddr', default='localhost')
    parser.add_argument('--labrad', action='store_true')
    parser.add_argument('--only-all', action='store_true')
    parser.add_argument('--skip-test', action='store_true')
    parser.add_argument('--output-sim-data', action='store_true')
    args = parser.parse_args()

    capture_modules = CaptureModule.all()
    if args.capture_module is not None:
        capture_modules = [CaptureModule.of(int(args.capture_module))]

    main(
        args.num_tests,
        args.ipaddr,
        capture_modules,
        args.labrad,
        args.server_ipaddr,
        args.only_all,
        args.skip_test,
        args.output_sim_data)
