from .rftooltransceiver import RftoolTransceiver
from .rfdcparam import RfdcParams
from .rfdcdefs import MixerScale

class RfdcValidator:

    def __init__(
        self,
        dac_tiles: set[int],
        dac_channels: set[int],
        rfdc_params: RfdcParams,
        interrupts: set[int]):
        self._dac_tiles = set(dac_tiles)
        self._dac_channels = set(dac_channels)
        self._rfdc_params = rfdc_params
        self._interrupts = interrupts
    
    def validate_transceiver(self, transceiver: RftoolTransceiver) -> None:
        if not isinstance(transceiver, RftoolTransceiver):
            raise ValueError('Invalid rftool transceiver {}'.format(transceiver))


    def validate_dac_tile(self, tile: int) -> None:
        if not tile in self._dac_tiles:
            raise ValueError('Invalid DAC tile {}'.format(tile))


    def validate_dac_channel(self, channel: int) -> None:
        if not channel in self._dac_channels:
            raise ValueError('Invalid DAC channel {}'.format(channel))
        

    def validate_mixer_freq(self, freq: float) -> None:
        min_freq = self._rfdc_params.min_mixer_freq()
        max_freq = self._rfdc_params.max_mixer_freq()
        if not (isinstance(freq, (float, int)) and (min_freq <= freq and freq <= max_freq)):
            raise ValueError(
                "A mixer frequency must be between {} and {} inclusive.  '{}' was set."
                .format(min_freq, max_freq, freq))


    def validate_mixer_phase(self, phase: float) -> None:
        inf_phase = self._rfdc_params.inf_mixer_phase()
        sup_phase = self._rfdc_params.sup_mixer_phase()
        if not (isinstance(phase, (float, int)) and (inf_phase < phase and phase < sup_phase)):
            raise ValueError(
                "A mixer phase must be greater than {} and less than {}.  '{}' was set."
                .format(inf_phase, sup_phase, phase))


    def validate_mixer_scale(self, scale: MixerScale) -> None:
        if not scale in set(MixerScale):
            raise ValueError('Invalid mixer scale {}'.format(scale))


    def validate_rfdc_interrupts(self, *flags: int) -> None:
        if not self._interrupts.issuperset(flags):
            raise ValueError('Invalid rfdc interrupt {}'.format(flags))
