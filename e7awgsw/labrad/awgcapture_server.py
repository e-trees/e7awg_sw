import pickle
import threading
import sys
from concurrent import futures
from labrad.server import ThreadedServer, setting
from labrad import util
from e7awgsw import AwgCtrl, CaptureCtrl

class AwgCaptureServer(ThreadedServer):

    name = 'Awg Capture Server'

    def __init__(self):
        pool = futures.ThreadPoolExecutor(max_workers=16)
        super().__init__(pool)
        self.__awgctrls = {}
        self.__capturectrls = {}
        self.__handle = 1
        self.__lock = threading.RLock()


    def __get_awgctrl(self, handle):
        with self.__lock:
            awgctrl = self.__awgctrls[handle]
        return awgctrl


    def __get_capturectrl(self, handle):
        with self.__lock:
            capturectrl = self.__capturectrls[handle]
        return capturectrl


    @setting(100, returns='y')
    def create_awgctrl(self, c, ipaddr):
        try:
            with self.__lock:
                handle = str(self.__handle)
                self.__awgctrls[handle] = AwgCtrl(ipaddr, validate_args = False)
                self.__handle += 1
        except Exception as e:
            return pickle.dumps(e)

        return pickle.dumps(str(handle))


    @setting(101, handle='s', returns='y')
    def discard_awgctrl(self, c, handle):
        try:
            with self.__lock:
                ctrl = self.__awgctrls.pop(handle)
                ctrl.close()
        except Exception as e:
            return pickle.dumps(e)
        
        return pickle.dumps(None)


    @setting(102, handle='s', awg_id='w', wave_seq='y', returns='y')
    def set_wave_sequence(self, c, handle, awg_id, wave_seq):
        try:
            wave_seq = pickle.loads(wave_seq)
            awgctrl = self.__get_awgctrl(handle)
            awgctrl.set_wave_sequence(awg_id, wave_seq)
        except Exception as e:
            return pickle.dumps(e)
        
        return pickle.dumps(None)


    @setting(103, handle='s', awg_id_list='*w', returns='y')
    def initialize_awgs(self, c, handle, awg_id_list):
        try:
            awgctrl = self.__get_awgctrl(handle)
            awgctrl.initialize(*awg_id_list)
        except Exception as e:
            return pickle.dumps(e)
        
        return pickle.dumps(None)


    @setting(104, handle='s', awg_id_list='*w', returns='y')
    def start_awgs(self, c, handle, awg_id_list):
        try:
            awgctrl = self.__get_awgctrl(handle)
            awgctrl.start_awgs(*awg_id_list)
        except Exception as e:
            return pickle.dumps(e)
        
        return pickle.dumps(None)


    @setting(105, handle='s', awg_id_list='*w', returns='y')
    def terminate_awgs(self, c, handle, awg_id_list):
        try:
            awgctrl = self.__get_awgctrl(handle)
            awgctrl.terminate_awgs(*awg_id_list)
        except Exception as e:
            return pickle.dumps(e)
        
        return pickle.dumps(None)


    @setting(106, handle='s', awg_id_list='*w', returns='y')
    def reset_awgs(self, c, handle, awg_id_list):
        try:
            awgctrl = self.__get_awgctrl(handle)
            awgctrl.reset_awgs(*awg_id_list)
        except Exception as e:
            return pickle.dumps(e)
        
        return pickle.dumps(None)


    @setting(107, handle='s', timeout='y', awg_id_list='*w', returns='y')
    def wait_for_awgs_to_stop(self, c, handle, timeout, awg_id_list):
        try:
            timeout = pickle.loads(timeout)
            awgctrl = self.__get_awgctrl(handle)
            awgctrl.wait_for_awgs_to_stop(timeout, *awg_id_list)
        except Exception as e:
            return pickle.dumps(e)
        
        return pickle.dumps(None)


    @setting(108, handle='s', interval='y', awg_id_list='*w', returns='y')
    def set_wave_startable_block_timing(self, c, handle, interval, awg_id_list):
        try:
            interval = pickle.loads(interval)
            awgctrl = self.__get_awgctrl(handle)
            awgctrl.set_wave_startable_block_timing(interval, *awg_id_list)
        except Exception as e:
            return pickle.dumps(e)
        
        return pickle.dumps(None)


    @setting(109, handle='s', awg_id_list='*w', returns='y')
    def get_wave_startable_block_timing(self, c, handle, awg_id_list):
        try:
            awgctrl = self.__get_awgctrl(handle)
            awg_id_to_interval = awgctrl.get_wave_startable_block_timing(*awg_id_list)
        except Exception as e:
            return pickle.dumps(e)
        
        return pickle.dumps(awg_id_to_interval)


    @setting(110, handle='s', awg_id_list='*w', returns='y')
    def check_awg_err(self, c, handle, awg_id_list):
        try:
            awgctrl = self.__get_awgctrl(handle)
            awg_id_to_err_list = awgctrl.check_err(*awg_id_list)
        except Exception as e:
            return pickle.dumps(e)
        
        return pickle.dumps(awg_id_to_err_list)


    @setting(111, handle='s', returns='y')
    def awg_version(self, c, handle):
        try:
            awgctrl = self.__get_awgctrl(handle)
            version = awgctrl.version()
        except Exception as e:
            return pickle.dumps(e)

        return pickle.dumps(version)


    @setting(112, handle='s', awg_id_list='*w', returns='y')
    def clear_awg_stop_flags(self, c, handle, awg_id_list):
        try:
            awgctrl = self.__get_awgctrl(handle)
            awgctrl.clear_awg_stop_flags(*awg_id_list)
        except Exception as e:
            return pickle.dumps(e)
        
        return pickle.dumps(None)


    @setting(200, returns='y')
    def create_capturectrl(self, c, ipaddr):
        try:
            with self.__lock:
                handle = str(self.__handle)
                self.__capturectrls[handle] = CaptureCtrl(ipaddr, validate_args = False)
                self.__handle += 1
        except Exception as e:
            return pickle.dumps(e)

        return pickle.dumps(str(handle))
        

    @setting(201, handle='s', returns='y')
    def discard_capturectrl(self, c, handle):
        try:
            with self.__lock:
                ctrl = self.__capturectrls.pop(handle)
                ctrl.close()
        except Exception as e:
            return pickle.dumps(e)

        return pickle.dumps(None)


    @setting(202, handle='s', capture_unit_id='w', param='y', returns='y')
    def set_capture_params(self, c, handle, capture_unit_id, param):
        try:
            param = pickle.loads(param)
            capturectrl = self.__get_capturectrl(handle)
            capturectrl.set_capture_params(capture_unit_id, param)
        except Exception as e:
            return pickle.dumps(e)

        return pickle.dumps(None)


    @setting(203, handle='s', capture_unit_id_list='*w', returns='y')
    def initialize_capture_units(self, c, handle, capture_unit_id_list):
        try:
            capturectrl = self.__get_capturectrl(handle)
            capturectrl.initialize(*capture_unit_id_list)
        except Exception as e:
            return pickle.dumps(e)

        return pickle.dumps(None)


    @setting(204, handle='s', capture_unit_id='w', num_samples='y', returns='y')
    def get_capture_data(self, c, handle, capture_unit_id, num_samples):
        try:
            num_samples = pickle.loads(num_samples)
            capturectrl = self.__get_capturectrl(handle)
            cap_data = capturectrl.get_capture_data(capture_unit_id, num_samples)
        except Exception as e:
            return pickle.dumps(e)

        return pickle.dumps(cap_data)

    
    @setting(205, handle='s', capture_unit_id='w', returns='y')
    def num_captured_samples(self, c, handle, capture_unit_id):
        try:
            capturectrl = self.__get_capturectrl(handle)
            num_samples = capturectrl.num_captured_samples(capture_unit_id)
        except Exception as e:
            return pickle.dumps(e)

        return pickle.dumps(num_samples)


    @setting(206, handle='s', capture_unit_id_list='*w', returns='y')
    def start_capture_units(self, c, handle, capture_unit_id_list):
        try:
            capturectrl = self.__get_capturectrl(handle)
            capturectrl.start_capture_units(*capture_unit_id_list)
        except Exception as e:
            return pickle.dumps(e)

        return pickle.dumps(None)


    @setting(207, handle='s', capture_unit_id_list='*w', returns='y')
    def reset_capture_units(self, c, handle, capture_unit_id_list):
        try:
            capturectrl = self.__get_capturectrl(handle)
            capturectrl.reset_capture_units(*capture_unit_id_list)
        except Exception as e:
            return pickle.dumps(e)

        return pickle.dumps(None)


    @setting(208, handle='s', capture_module_id='w', awg_id='w', returns='y')
    def select_trigger_awg(self, c, handle, capture_module_id, awg_id):
        try:
            capturectrl = self.__get_capturectrl(handle)
            capturectrl.select_trigger_awg(capture_module_id, awg_id)
        except Exception as e:
            return pickle.dumps(e)

        return pickle.dumps(None)


    @setting(209, handle='s', capture_unit_id_list='*w', returns='y')
    def enable_start_trigger(self, c, handle, capture_unit_id_list):
        try:
            capturectrl = self.__get_capturectrl(handle)
            capturectrl.enable_start_trigger(*capture_unit_id_list)
        except Exception as e:
            return pickle.dumps(e)

        return pickle.dumps(None)


    @setting(210, handle='s', capture_unit_id_list='*w', returns='y')
    def disable_start_trigger(self, c, handle, capture_unit_id_list):
        try:
            capturectrl = self.__get_capturectrl(handle)
            capturectrl.disable_start_trigger(*capture_unit_id_list)
        except Exception as e:
            return pickle.dumps(e)

        return pickle.dumps(None)


    @setting(211, handle='s', timeout='y', capture_unit_id_list='*w', returns='y')
    def wait_for_capture_units_to_stop(self, c, handle, timeout, capture_unit_id_list):
        try:
            timeout = pickle.loads(timeout)
            capturectrl = self.__get_capturectrl(handle)
            capturectrl.wait_for_capture_units_to_stop(timeout, *capture_unit_id_list)
        except Exception as e:
            return pickle.dumps(e)

        return pickle.dumps(None)


    @setting(212, handle='s', capture_unit_id_list='*w', returns='y')
    def check_capture_unit_err(self, c, handle, capture_unit_id_list):
        try:
            capturectrl = self.__get_capturectrl(handle)
            cap_unit_id_to_err_list = capturectrl.check_err(*capture_unit_id_list)
        except Exception as e:
            return pickle.dumps(e)

        return pickle.dumps(cap_unit_id_to_err_list)


    @setting(213, handle='s', returns='y')
    def capture_unit_version(self, c, handle):
        try:
            capturectrl = self.__get_capturectrl(handle)
            version = capturectrl.version()
        except Exception as e:
            return pickle.dumps(e)

        return pickle.dumps(version)


    @setting(214, handle='s', capture_unit_id='w', num_samples='y', returns='y')
    def get_classification_results(self, c, handle, capture_unit_id, num_samples):
        try:
            num_samples = pickle.loads(num_samples)
            capturectrl = self.__get_capturectrl(handle)
            cap_data = capturectrl.get_classification_results(capture_unit_id, num_samples)
        except Exception as e:
            return pickle.dumps(e)

        return pickle.dumps(cap_data)


    @setting(215, handle='s', capture_unit_id_list='*w', returns='y')
    def clear_capture_stop_flags(self, c, handle, capture_unit_id_list):
        try:
            capturectrl = self.__get_capturectrl(handle)
            capturectrl.clear_capture_stop_flags(*capture_unit_id_list)
        except Exception as e:
            return pickle.dumps(e)

        return pickle.dumps(None)


__server__ = AwgCaptureServer()

if __name__ == '__main__':
    util.runServer(__server__)
