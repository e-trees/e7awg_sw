from e7awgsw.feedback.hwparam import CLASSIFICATION_RESULT_SIZE, CAPTURED_SAMPLE_SIZE, CAPTURE_DATA_ALIGNMENT_SIZE
from e7awgsw.feedback.hwdefs import DspUnit
from e7awgsw.logger import log_error
from e7awgsw.captureparam import CaptureParam

class CaptureParamFeedback(CaptureParam):
    def del_sum_section(self, index):
        """引数で指定したインデックスの総和区間を削除する

        Args:
            index (int): 削除する総和区間のインデックス (0 ~ 登録済みの総和区間数 - 1)
        """
        if index >= len(self.__sumsections):
            msg = "Invalid index  ({}).  This capture parameter has only {} sum sections.".format(
                index, len(self.__sumsections))
            log_error(msg, *self.__loggers)
            raise ValueError(msg)

        del self.__sumsections[index]

    def calc_required_capture_mem_size(self):
        """現在のキャプチャパラメータでのキャプチャに必要な RAM のサイズを計算する

        Returns:
            int: キャプチャに必要な RAM のサイズ (bytes)
        """
        if DspUnit.CLASSIFICATION in self.dsp_units_enabled:
            num_bits = self.calc_capture_samples() * CLASSIFICATION_RESULT_SIZE
            return -(-num_bits // (CAPTURE_DATA_ALIGNMENT_SIZE * 8)) * CAPTURE_DATA_ALIGNMENT_SIZE

        num_bytes = self.calc_capture_samples() * CAPTURED_SAMPLE_SIZE
        return -(-num_bytes // CAPTURE_DATA_ALIGNMENT_SIZE) * CAPTURE_DATA_ALIGNMENT_SIZE
