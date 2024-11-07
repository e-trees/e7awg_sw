import pickle
import threading
from concurrent import futures
from labrad.server import ThreadedServer, setting  # type: ignore
from labrad import util  # type: ignore
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
            return self.__awgctrls[handle]


    def __get_capturectrl(self, handle):
        with self.__lock:
            return self.__capturectrls[handle]


    @setting(100, ipaddr='s', design_type='y', returns='y')
    def create_awgctrl(self, c, ipaddr, design_type):
        try:
            with self.__lock:
                handle = str(self.__handle)
                design_type = pickle.loads(design_type)
                self.__awgctrls[handle] = AwgCtrl(ipaddr, design_type, validate_args = False)
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


    @setting(113, handle='s', returns='y')
    def awg_sampling_rate(self, c, handle):
        try:
            awgctrl = self.__get_awgctrl(handle)
            sampling_rate = awgctrl.sampling_rate()
            return pickle.dumps(sampling_rate)
        except Exception as e:
            return pickle.dumps(e)


    @setting(114, handle='s', awg_id_list='*w', returns='y')
    def prepare_awgs(self, c, handle, awg_id_list):
        try:
            awgctrl = self.__get_awgctrl(handle)
            awgctrl.prepare_awgs(*awg_id_list)
            return pickle.dumps(None)
        except Exception as e:
            return pickle.dumps(e)


    @setting(200, ipaddr='s', design_type='y', returns='y')
    def create_capturectrl(self, c, ipaddr, design_type):
        try:
            with self.__lock:
                handle = str(self.__handle)
                design_type = pickle.loads(design_type)
                self.__capturectrls[handle] = CaptureCtrl(ipaddr, design_type, validate_args = False)
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
            offset = pickle.loads(addr_offset)
            capturectrl = self.__get_capturectrl(handle)
            cap_data = capturectrl.get_capture_data(capture_unit_id, num_samples, offset)
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
            offset = pickle.loads(addr_offset)
            capturectrl = self.__get_capturectrl(handle)
            cap_data = capturectrl.get_classification_results(capture_unit_id, num_samples, offset)
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


    @setting(216, handle='s', timeout='y', capture_unit_id_list='*w', returns='y')
    def wait_for_capture_units_idle(self, c, handle, timeout, capture_unit_id_list):
        try:
            timeout = pickle.loads(timeout)
            capturectrl = self.__get_capturectrl(handle)
            capturectrl.wait_for_capture_units_idle(timeout, *capture_unit_id_list)
            return pickle.dumps(None)
        except Exception as e:
            return pickle.dumps(e)


    @setting(217, handle='s', capture_module_id='w', capture_unit_id_list='*w', returns='y')
    def construct_capture_module(self, c, handle, capture_module_id, capture_unit_id_list):
        try:
            capturectrl = self.__get_capturectrl(handle)
            capturectrl.construct_capture_module(capture_module_id, *capture_unit_id_list)
            return pickle.dumps(None)
        except Exception as e:
            return pickle.dumps(e)


    @setting(218, handle='s', returns='y')
    def get_unit_to_module(self, c, handle):
        try:
            capturectrl = self.__get_capturectrl(handle)
            unit_to_mod = capturectrl.get_unit_to_module()
            return pickle.dumps(unit_to_mod)
        except Exception as e:
            return pickle.dumps(e)


    @setting(219, handle='s', returns='y')
    def get_module_to_units(self, c, handle):
        try:
            capturectrl = self.__get_capturectrl(handle)
            mod_to_units = capturectrl.get_module_to_units()
            return pickle.dumps(mod_to_units)
        except Exception as e:
            return pickle.dumps(e)


    @setting(220, handle='s', returns='y')
    def get_module_to_trigger(self, c, handle):
        try:
            capturectrl = self.__get_capturectrl(handle)
            mod_to_trig = capturectrl.get_module_to_trigger()
            return pickle.dumps(mod_to_trig)
        except Exception as e:
            return pickle.dumps(e)


    @setting(221, handle='s', returns='y')
    def get_trigger_to_modules(self, c, handle):
        try:
            capturectrl = self.__get_capturectrl(handle)
            trig_to_mods = capturectrl.get_trigger_to_modules()
            return pickle.dumps(trig_to_mods)
        except Exception as e:
            return pickle.dumps(e)


    @setting(222, handle='s', capture_unit_id_list='*w', returns='y')
    def get_capture_stop_flags(self, c, handle, capture_unit_id_list):
        try:
            capturectrl = self.__get_capturectrl(handle)
            flags = capturectrl._get_capture_stop_flags(*capture_unit_id_list)
            return pickle.dumps(flags)
        except Exception as e:
            return pickle.dumps(e)
        

    @setting(223, handle='s', returns='y')
    def max_capture_samples(self, c, handle):
        try:
            capturectrl = self.__get_capturectrl(handle)
            max_cap_samples = capturectrl.max_capture_samples()
            return pickle.dumps(max_cap_samples)
        except Exception as e:
            return pickle.dumps(e)


    @setting(224, handle='s', returns='y')
    def max_classification_results(self, c, handle):
        try:
            capturectrl = self.__get_capturectrl(handle)
            max_cls_results = capturectrl.max_classification_results()
            return pickle.dumps(max_cls_results)
        except Exception as e:
            return pickle.dumps(e)


    @setting(225, handle='s', returns='y')
    def capture_unit_sampling_rate(self, c, handle):
        try:
            capturectrl = self.__get_capturectrl(handle)
            sampling_rate = capturectrl.sampling_rate()
            return pickle.dumps(sampling_rate)
        except Exception as e:
            return pickle.dumps(e)


__server__ = AwgCaptureServer()

if __name__ == '__main__':
    util.runServer(__server__)
