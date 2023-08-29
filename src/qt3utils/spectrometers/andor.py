from .atspectrograph import ATSpectrograph
from .interface import DiffractionController, SpectrometerDetector
from ..load_lib import load_library


class Shamrock750Spectrograph(DiffractionController):

    def __init__(self, device_id, lib_path=None):
        lib_paths = [lib_path] + ATSpectrograph.DEFAULT_PATHS \
            if lib_path is not None else ATSpectrograph.DEFAULT_PATHS

        load_library(ATSpectrograph.DEFAULT_LIBRARY_NAME, lib_paths, ATSpectrograph.DEFAULT_REGISTRY_NAME)
        self.atspectrograph = ATSpectrograph()

        self.device_id = device_id

    def init(self):
        result: int = self.atspectrograph.Initialize()
        if result != ATSpectrograph.ReturnCodes.SUCCESS:
            raise RuntimeError(f'Unable to initialize {self.__name__} with error code: '
                               f'{ATSpectrograph.ReturnCodes(result)}.')

        _, no_devices = self.atspectrograph.GetNumberDevices()
        if no_devices <= 0:
            raise RuntimeError(f'No {self.__name__} devices were found.')

        if self.device_id > no_devices:
            raise ValueError(f'The provided device id for {self.__name__} is larger than the number of available'
                             f' devices ({no_devices})')

        # TODO: Maybe set up grating information?

    def close(self):
        result: int = self.atspectrograph.Close()
        if result != ATSpectrograph.ReturnCodes.SUCCESS:
            raise RuntimeError(f'Unable to close {self.__name__} with error code: '
                               f'{ATSpectrograph.ReturnCodes(result)}.')

    def get_available_gratings(self) -> list[Any]:
        raise NotImplementedError()

    def get_grating(self) -> float:
        raise NotImplementedError()

    def set_grating(self, grating: Any):
        raise NotImplementedError()

    def get_center_wavelength(self) -> float:
        raise NotImplementedError()

    def set_center_wavelength(self, wavelength: float):
        raise NotImplementedError()


class NewtonCCD(SpectrometerDetector):

    def init(self):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()

    def get_temperature(self) -> float:
        raise NotImplementedError()

    def set_temperature(self, temperature: float):
        raise NotImplementedError()

    def get_exposure_time(self) -> float:
        raise NotImplementedError()

    def set_exposure_time(self, exposure_time: float):
        raise NotImplementedError()

    def acquire_single_frame(self, *args):
        raise NotImplementedError()

    def acquire_kinetic_series(self, *args):
        raise NotImplementedError()

    def acquire_step_and_glue(self, *args):
        raise NotImplementedError()
