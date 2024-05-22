import pickle
import threading
from concurrent import futures
from labrad.server import ThreadedServer, setting  # type: ignore
from labrad import util  # type: ignore
from e7awgsw import AwgCtrl, CaptureCtrl, SequencerCtrl

class AwgCaptureServer(ThreadedServer):

    name = 'Awg Capture Server'

    def __init__(self):
        pool = futures.ThreadPoolExecutor(max_workers=16)
        super().__init__(pool)
        self.__awgctrls = {}
        self.__capturectrls = {}
        self.__sequencerctrls = {}
        self.__handle = 1
        self.__lock = threading.RLock()


    def __get_awgctrl(self, handle):
        with self.__lock:
            return self.__awgctrls[handle]


    def __get_capturectrl(self, handle):
        with self.__lock:
            return self.__capturectrls[handle]


    def __get_sequencerctrl(self, handle):
        with self.__lock:
            return self.__sequencerctrls[handle]


    @setting(100, returns='y')
    def create_awgctrl(self, c, ipaddr):
        try:
            with self.__lock:
                handle = str(self.__handle)
                self.__awgctrls[handle] = AwgCtrl(ipaddr, validate_args = False)
                self.__handle += 1
            return pickle.dumps(str(handle))
        except Exception as e:
            return pickle.dumps(e)


    @setting(101, handle='s', returns='y')
    def discard_awgctrl(self, c, handle):
        try:
            with self.__lock:
                ctrl = self.__awgctrls.pop(handle)
                ctrl.close()
            return pickle.dumps(None)
        except Exception as e:
            return pickle.dumps(e)
        

    @setting(102, handle='s', awg_id='w', wave_seq='y', returns='y')
    def set_wave_sequence(self, c, handle, awg_id, wave_seq):
        try:
            wave_seq = pickle.loads(wave_seq)
            awgctrl = self.__get_awgctrl(handle)
            awgctrl.set_wave_sequence(awg_id, wave_seq)
            return pickle.dumps(None)
        except Exception as e:
            return pickle.dumps(e)
        

    @setting(103, handle='s', awg_id_list='*w', returns='y')
    def initialize_awgs(self, c, handle, awg_id_list):
        try:
            awgctrl = self.__get_awgctrl(handle)
            awgctrl.initialize(*awg_id_list)
            return pickle.dumps(None)
        except Exception as e:
            return pickle.dumps(e)
        

    @setting(104, handle='s', awg_id_list='*w', returns='y')
    def start_awgs(self, c, handle, awg_id_list):
        try:
            awgctrl = self.__get_awgctrl(handle)
            awgctrl.start_awgs(*awg_id_list)
            return pickle.dumps(None)
        except Exception as e:
            return pickle.dumps(e)
        
    
    @setting(105, handle='s', awg_id_list='*w', returns='y')
    def terminate_awgs(self, c, handle, awg_id_list):
        try:
            awgctrl = self.__get_awgctrl(handle)
            awgctrl.terminate_awgs(*awg_id_list)
            return pickle.dumps(None)
        except Exception as e:
            return pickle.dumps(e)
        

    @setting(106, handle='s', awg_id_list='*w', returns='y')
    def reset_awgs(self, c, handle, awg_id_list):
        try:
            awgctrl = self.__get_awgctrl(handle)
            awgctrl.reset_awgs(*awg_id_list)
            return pickle.dumps(None)
        except Exception as e:
            return pickle.dumps(e)


    @setting(107, handle='s', timeout='y', awg_id_list='*w', returns='y')
    def wait_for_awgs_to_stop(self, c, handle, timeout, awg_id_list):
        try:
            timeout = pickle.loads(timeout)
            awgctrl = self.__get_awgctrl(handle)
            awgctrl.wait_for_awgs_to_stop(timeout, *awg_id_list)
            return pickle.dumps(None)
        except Exception as e:
            return pickle.dumps(e)


    @setting(108, handle='s', interval='y', awg_id_list='*w', returns='y')
    def set_wave_startable_block_timing(self, c, handle, interval, awg_id_list):
        try:
            interval = pickle.loads(interval)
            awgctrl = self.__get_awgctrl(handle)
            awgctrl.set_wave_startable_block_timing(interval, *awg_id_list)
            return pickle.dumps(None)
        except Exception as e:
            return pickle.dumps(e)
        

    @setting(109, handle='s', awg_id_list='*w', returns='y')
    def get_wave_startable_block_timing(self, c, handle, awg_id_list):
        try:
            awgctrl = self.__get_awgctrl(handle)
            awg_id_to_interval = awgctrl.get_wave_startable_block_timing(*awg_id_list)
            return pickle.dumps(awg_id_to_interval)
        except Exception as e:
            return pickle.dumps(e)
        

    @setting(110, handle='s', awg_id_list='*w', returns='y')
    def check_awg_err(self, c, handle, awg_id_list):
        try:
            awgctrl = self.__get_awgctrl(handle)
            awg_id_to_err_list = awgctrl.check_err(*awg_id_list)
            return pickle.dumps(awg_id_to_err_list)
        except Exception as e:
            return pickle.dumps(e)
        

    @setting(111, handle='s', returns='y')
    def awg_version(self, c, handle):
        try:
            awgctrl = self.__get_awgctrl(handle)
            version = awgctrl.version()
            return pickle.dumps(version)
        except Exception as e:
            return pickle.dumps(e)


    @setting(112, handle='s', awg_id_list='*w', returns='y')
    def clear_awg_stop_flags(self, c, handle, awg_id_list):
        try:
            awgctrl = self.__get_awgctrl(handle)
            awgctrl.clear_awg_stop_flags(*awg_id_list)
            return pickle.dumps(None)
        except Exception as e:
            return pickle.dumps(e)
        

    @setting(113, handle='s', awg_id='w', key_to_wave_seq='y', returns='y')
    def register_wave_sequences(self, c, handle, awg_id, key_to_wave_seq):
        try:
            key_to_wave_seq = pickle.loads(key_to_wave_seq)
            awgctrl = self.__get_awgctrl(handle)
            awgctrl.register_wave_sequences(awg_id, key_to_wave_seq)
            return pickle.dumps(None)
        except Exception as e:
            return pickle.dumps(e)
        

    @setting(200, returns='y')
    def create_capturectrl(self, c, ipaddr):
        try:
            with self.__lock:
                handle = str(self.__handle)
                self.__capturectrls[handle] = CaptureCtrl(ipaddr, validate_args = False)
                self.__handle += 1
            return pickle.dumps(str(handle))
        except Exception as e:
            return pickle.dumps(e)
        

    @setting(201, handle='s', returns='y')
    def discard_capturectrl(self, c, handle):
        try:
            with self.__lock:
                ctrl = self.__capturectrls.pop(handle)
                ctrl.close()
            return pickle.dumps(None)
        except Exception as e:
            return pickle.dumps(e)


    @setting(202, handle='s', capture_unit_id='w', param='y', returns='y')
    def set_capture_params(self, c, handle, capture_unit_id, param):
        try:
            param = pickle.loads(param)
            capturectrl = self.__get_capturectrl(handle)
            capturectrl.set_capture_params(capture_unit_id, param)
            return pickle.dumps(None)
        except Exception as e:
            return pickle.dumps(e)


    @setting(203, handle='s', capture_unit_id_list='*w', returns='y')
    def initialize_capture_units(self, c, handle, capture_unit_id_list):
        try:
            capturectrl = self.__get_capturectrl(handle)
            capturectrl.initialize(*capture_unit_id_list)
            return pickle.dumps(None)
        except Exception as e:
            return pickle.dumps(e)


    @setting(204, handle='s', capture_unit_id='w', num_samples='y', addr_offset='y', returns='y')
    def get_capture_data(self, c, handle, capture_unit_id, num_samples, addr_offset):
        try:
            num_samples = pickle.loads(num_samples)
            addr_offset = pickle.loads(addr_offset)
            capturectrl = self.__get_capturectrl(handle)
            cap_data = capturectrl.get_capture_data(capture_unit_id, num_samples, addr_offset)
            return pickle.dumps(cap_data)
        except Exception as e:
            return pickle.dumps(e)

    
    @setting(205, handle='s', capture_unit_id='w', returns='y')
    def num_captured_samples(self, c, handle, capture_unit_id):
        try:
            capturectrl = self.__get_capturectrl(handle)
            num_samples = capturectrl.num_captured_samples(capture_unit_id)
            return pickle.dumps(num_samples)
        except Exception as e:
            return pickle.dumps(e)


    @setting(206, handle='s', capture_unit_id_list='*w', returns='y')
    def start_capture_units(self, c, handle, capture_unit_id_list):
        try:
            capturectrl = self.__get_capturectrl(handle)
            capturectrl.start_capture_units(*capture_unit_id_list)
            return pickle.dumps(None)
        except Exception as e:
            return pickle.dumps(e)


    @setting(207, handle='s', capture_unit_id_list='*w', returns='y')
    def reset_capture_units(self, c, handle, capture_unit_id_list):
        try:
            capturectrl = self.__get_capturectrl(handle)
            capturectrl.reset_capture_units(*capture_unit_id_list)
            return pickle.dumps(None)
        except Exception as e:
            return pickle.dumps(e)


    @setting(208, handle='s', capture_module_id='w', awg_id='y', returns='y')
    def select_trigger_awg(self, c, handle, capture_module_id, awg_id):
        try:
            awg_id = pickle.loads(awg_id) # None の可能性があるので bytes で受ける
            capturectrl = self.__get_capturectrl(handle)
            capturectrl.select_trigger_awg(capture_module_id, awg_id)
            return pickle.dumps(None)
        except Exception as e:
            return pickle.dumps(e)


    @setting(209, handle='s', capture_unit_id_list='*w', returns='y')
    def enable_start_trigger(self, c, handle, capture_unit_id_list):
        try:
            capturectrl = self.__get_capturectrl(handle)
            capturectrl.enable_start_trigger(*capture_unit_id_list)
            return pickle.dumps(None)
        except Exception as e:
            return pickle.dumps(e)

    
    @setting(210, handle='s', capture_unit_id_list='*w', returns='y')
    def disable_start_trigger(self, c, handle, capture_unit_id_list):
        try:
            capturectrl = self.__get_capturectrl(handle)
            capturectrl.disable_start_trigger(*capture_unit_id_list)
            return pickle.dumps(None)
        except Exception as e:
            return pickle.dumps(e)


    @setting(211, handle='s', timeout='y', capture_unit_id_list='*w', returns='y')
    def wait_for_capture_units_to_stop(self, c, handle, timeout, capture_unit_id_list):
        try:
            timeout = pickle.loads(timeout)
            capturectrl = self.__get_capturectrl(handle)
            capturectrl.wait_for_capture_units_to_stop(timeout, *capture_unit_id_list)
            return pickle.dumps(None)
        except Exception as e:
            return pickle.dumps(e)


    @setting(212, handle='s', capture_unit_id_list='*w', returns='y')
    def check_capture_unit_err(self, c, handle, capture_unit_id_list):
        try:
            capturectrl = self.__get_capturectrl(handle)
            cap_unit_id_to_err_list = capturectrl.check_err(*capture_unit_id_list)
            return pickle.dumps(cap_unit_id_to_err_list)
        except Exception as e:
            return pickle.dumps(e)


    @setting(213, handle='s', returns='y')
    def capture_unit_version(self, c, handle):
        try:
            capturectrl = self.__get_capturectrl(handle)
            version = capturectrl.version()
            return pickle.dumps(version)
        except Exception as e:
            return pickle.dumps(e)


    @setting(214, handle='s', capture_unit_id='w', num_samples='y', addr_offset='y', returns='y')
    def get_classification_results(self, c, handle, capture_unit_id, num_samples, addr_offset):
        try:
            num_samples = pickle.loads(num_samples)
            addr_offset = pickle.loads(addr_offset)
            capturectrl = self.__get_capturectrl(handle)
            cap_data = capturectrl.get_classification_results(capture_unit_id, num_samples, addr_offset)
            return pickle.dumps(cap_data)
        except Exception as e:
            return pickle.dumps(e)


    @setting(215, handle='s', capture_unit_id_list='*w', returns='y')
    def clear_capture_stop_flags(self, c, handle, capture_unit_id_list):
        try:
            capturectrl = self.__get_capturectrl(handle)
            capturectrl.clear_capture_stop_flags(*capture_unit_id_list)
            return pickle.dumps(None)
        except Exception as e:
            return pickle.dumps(e)


    @setting(216, handle='s', key='y', param='y', returns='y')
    def register_capture_params(self, c, handle, key, param):
        try:
            key = pickle.loads(key)
            param = pickle.loads(param)
            capturectrl = self.__get_capturectrl(handle)
            capturectrl.register_capture_params(key, param)
            return pickle.dumps(None)
        except Exception as e:
            return pickle.dumps(e)


    @setting(217, handle='s', timeout='y', capture_unit_id_list='*w', returns='y')
    def wait_for_capture_units_idle(self, c, handle, timeout, capture_unit_id_list):
        try:
            timeout = pickle.loads(timeout)
            capturectrl = self.__get_capturectrl(handle)
            capturectrl.wait_for_capture_units_idle(timeout, *capture_unit_id_list)
            return pickle.dumps(None)
        except Exception as e:
            return pickle.dumps(e)


    @setting(218, handle='s', capture_module_id='w', capture_unit_id_list='*w', returns='y')
    def construct_capture_module(self, c, handle, capture_module_id, capture_unit_id_list):
        try:
            capturectrl = self.__get_capturectrl(handle)
            capturectrl.construct_capture_module(capture_module_id, *capture_unit_id_list)
            return pickle.dumps(None)
        except Exception as e:
            return pickle.dumps(e)


    @setting(219, handle='s', returns='y')
    def get_unit_to_module(self, c, handle):
        try:
            capturectrl = self.__get_capturectrl(handle)
            unit_to_mod = capturectrl.get_unit_to_module()
            return pickle.dumps(unit_to_mod)
        except Exception as e:
            return pickle.dumps(e)


    @setting(220, handle='s', returns='y')
    def get_module_to_units(self, c, handle):
        try:
            capturectrl = self.__get_capturectrl(handle)
            mod_to_units = capturectrl.get_module_to_units()
            return pickle.dumps(mod_to_units)
        except Exception as e:
            return pickle.dumps(e)


    @setting(221, handle='s', returns='y')
    def get_module_to_trigger(self, c, handle):
        try:
            capturectrl = self.__get_capturectrl(handle)
            mod_to_trig = capturectrl.get_module_to_trigger()
            return pickle.dumps(mod_to_trig)
        except Exception as e:
            return pickle.dumps(e)


    @setting(222, handle='s', returns='y')
    def get_trigger_to_modules(self, c, handle):
        try:
            capturectrl = self.__get_capturectrl(handle)
            trig_to_mods = capturectrl.get_trigger_to_modules()
            return pickle.dumps(trig_to_mods)
        except Exception as e:
            return pickle.dumps(e)


    @setting(223, handle='s', capture_unit_id_list='*w', returns='y')
    def get_capture_stop_flags(self, c, handle, capture_unit_id_list):
        try:
            capturectrl = self.__get_capturectrl(handle)
            flags = capturectrl._get_capture_stop_flags(*capture_unit_id_list)
            return pickle.dumps(flags)
        except Exception as e:
            return pickle.dumps(e)



    @setting(300, returns='y')
    def create_sequencerctrl(self, c, ipaddr):
        try:
            with self.__lock:
                handle = str(self.__handle)
                self.__sequencerctrls[handle] = SequencerCtrl(ipaddr, validate_args = False)
                self.__handle += 1
            return pickle.dumps(str(handle))
        except Exception as e:
            return pickle.dumps(e)


    @setting(301, handle='s', returns='y')
    def discard_sequencerctrl(self, c, handle):
        try:
            with self.__lock:
                ctrl = self.__sequencerctrls.pop(handle)
                ctrl.close()
            return pickle.dumps(None)
        except Exception as e:
            return pickle.dumps(e)
        

    @setting(302, handle='s', returns='y')
    def initialize_sequencer(self, c, handle):
        try:
            seqencerctrl = self.__get_sequencerctrl(handle)
            seqencerctrl.initialize()
            return pickle.dumps(None)
        except Exception as e:
            return pickle.dumps(e)
        

    @setting(303, handle='s', cmd_list='y', returns='y')
    def push_commands(self, c, handle, cmd_list):
        try:
            cmd_list = pickle.loads(cmd_list)
            seqencerctrl = self.__get_sequencerctrl(handle)
            seqencerctrl.push_commands(cmd_list)
            return pickle.dumps(None)
        except Exception as e:
            return pickle.dumps(e)


    @setting(304, handle='s', returns='y')
    def start_sequencer(self, c, handle):
        try:
            seqencerctrl = self.__get_sequencerctrl(handle)
            seqencerctrl.start_sequencer()
            return pickle.dumps(None)
        except Exception as e:
            return pickle.dumps(e)
        

    @setting(305, handle='s', returns='y')
    def terminate_sequencer(self, c, handle):
        try:
            seqencerctrl = self.__get_sequencerctrl(handle)
            seqencerctrl.terminate_sequencer()
            return pickle.dumps(None)
        except Exception as e:
            return pickle.dumps(e)
        

    @setting(306, handle='s', returns='y')
    def clear_commands(self, c, handle):
        try:
            seqencerctrl = self.__get_sequencerctrl(handle)
            seqencerctrl.clear_commands()
            return pickle.dumps(None)
        except Exception as e:
            return pickle.dumps(e)
        

    @setting(307, handle='s', returns='y')
    def clear_unsent_cmd_err_reports(self, c, handle):
        try:
            seqencerctrl = self.__get_sequencerctrl(handle)
            seqencerctrl.clear_unsent_cmd_err_reports()
            return pickle.dumps(None)
        except Exception as e:
            return pickle.dumps(e)
        

    @setting(308, handle='s', returns='y')
    def clear_sequencer_stop_flag(self, c, handle):
        try:
            seqencerctrl = self.__get_sequencerctrl(handle)
            seqencerctrl.clear_sequencer_stop_flag()
            return pickle.dumps(None)
        except Exception as e:
            return pickle.dumps(e)
        

    @setting(309, handle='s', returns='y')
    def enable_cmd_err_report(self, c, handle):
        try:
            seqencerctrl = self.__get_sequencerctrl(handle)
            seqencerctrl.enable_cmd_err_report()
            return pickle.dumps(None)
        except Exception as e:
            return pickle.dumps(e)
        

    @setting(310, handle='s', returns='y')
    def disable_cmd_err_report(self, c, handle):
        try:
            seqencerctrl = self.__get_sequencerctrl(handle)
            seqencerctrl.disable_cmd_err_report()
            return pickle.dumps(None)
        except Exception as e:
            return pickle.dumps(e)
        

    @setting(311, handle='s', timeout='y', returns='y')
    def wait_for_sequencer_to_stop(self, c, handle, timeout):
        try:
            timeout = pickle.loads(timeout)
            seqencerctrl = self.__get_sequencerctrl(handle)
            seqencerctrl.wait_for_sequencer_to_stop(timeout)
            return pickle.dumps(None)
        except Exception as e:
            return pickle.dumps(e)


    @setting(312, handle='s', returns='y')
    def num_unprocessed_commands(self, c, handle):
        try:
            seqencerctrl = self.__get_sequencerctrl(handle)
            num_unprocessed_commands = seqencerctrl.num_unprocessed_commands()
            return pickle.dumps(num_unprocessed_commands)
        except Exception as e:
            return pickle.dumps(e)


    @setting(313, handle='s', returns='y')
    def num_successful_commands(self, c, handle):
        try:
            seqencerctrl = self.__get_sequencerctrl(handle)
            num_successful_commands = seqencerctrl.num_successful_commands()
            return pickle.dumps(num_successful_commands)
        except Exception as e:
            return pickle.dumps(e)


    @setting(314, handle='s', returns='y')
    def num_err_commands(self, c, handle):
        try:
            seqencerctrl = self.__get_sequencerctrl(handle)
            num_err_commands = seqencerctrl.num_err_commands()
            return pickle.dumps(num_err_commands)
        except Exception as e:
            return pickle.dumps(e)


    @setting(315, handle='s', returns='y')
    def num_unsent_cmd_err_reports(self, c, handle):
        try:
            seqencerctrl = self.__get_sequencerctrl(handle)
            num_unsent_cmd_err_reports = seqencerctrl.num_unsent_cmd_err_reports()
            return pickle.dumps(num_unsent_cmd_err_reports)
        except Exception as e:
            return pickle.dumps(e)


    @setting(316, handle='s', returns='y')
    def cmd_fifo_free_space(self, c, handle):
        try:
            seqencerctrl = self.__get_sequencerctrl(handle)
            cmd_fifo_free_space = seqencerctrl.cmd_fifo_free_space()
            return pickle.dumps(cmd_fifo_free_space)
        except Exception as e:
            return pickle.dumps(e)


    @setting(317, handle='s', returns='y')
    def check_sequencer_err(self, c, handle):
        try:
            seqencerctrl = self.__get_sequencerctrl(handle)
            err_list = seqencerctrl.check_err()
            return pickle.dumps(err_list)
        except Exception as e:
            return pickle.dumps(e)


    @setting(318, handle='s', returns='y')
    def pop_cmd_err_reports(self, c, handle):
        try:
            seqencerctrl = self.__get_sequencerctrl(handle)
            cmd_err_reports = seqencerctrl.pop_cmd_err_reports()
            return pickle.dumps(cmd_err_reports)
        except Exception as e:
            return pickle.dumps(e)


    @setting(319, handle='s', returns='y')
    def sequencer_version(self, c, handle):
        try:
            seqencerctrl = self.__get_sequencerctrl(handle)
            version = seqencerctrl.version()
            return pickle.dumps(version)
        except Exception as e:
            return pickle.dumps(e)
        

    @setting(320, handle='s', returns='y')
    def num_stored_commands(self, c, handle):
        try:
            seqencerctrl = self.__get_sequencerctrl(handle)
            num_stored_commands = seqencerctrl._num_stored_commands()
            return pickle.dumps(num_stored_commands)
        except Exception as e:
            return pickle.dumps(e)


    @setting(321, handle='s', returns='y')
    def cmd_counter(self, c, handle):
        try:
            seqencerctrl = self.__get_sequencerctrl(handle)
            cmd_counter = seqencerctrl._cmd_counter()
            return pickle.dumps(cmd_counter)
        except Exception as e:
            return pickle.dumps(e)


    @setting(322, handle='s', returns='y')
    def reset_cmd_counter(self, c, handle):
        try:
            seqencerctrl = self.__get_sequencerctrl(handle)
            seqencerctrl._reset_cmd_counter()
            return pickle.dumps(None)
        except Exception as e:
            return pickle.dumps(e)
    

    @setting(323, handle='s', returns='y')
    def get_branch_flag(self, c, handle):
        try:
            seqencerctrl = self.__get_sequencerctrl(handle)
            return pickle.dumps(seqencerctrl.get_branch_flag())
        except Exception as e:
            return pickle.dumps(e)


    @setting(324, handle='s', val='b', returns='y')
    def set_branch_flag(self, c, handle, val):
        try:
            seqencerctrl = self.__get_sequencerctrl(handle)
            seqencerctrl.set_branch_flag(val)
            return pickle.dumps(None)
        except Exception as e:
            return pickle.dumps(e)


    @setting(325, handle='s', returns='y')
    def get_external_branch_flag(self, c, handle):
        try:
            seqencerctrl = self.__get_sequencerctrl(handle)
            return pickle.dumps(seqencerctrl._get_external_branch_flag())
        except Exception as e:
            return pickle.dumps(e)


__server__ = AwgCaptureServer()

if __name__ == '__main__':
    util.runServer(__server__)
