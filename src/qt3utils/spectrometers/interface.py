import abc
from typing import Any


class DiffractionController(abc.ABC):

    @abc.abstractmethod(classmethod)
    def init(self):
        raise NotImplementedError()

    @abc.abstractmethod(classmethod)
    def close(self):
        raise NotImplementedError()

    @abc.abstractmethod(classmethod)
    def get_available_gratings(self) -> list[Any]:
        raise NotImplementedError()

    @abc.abstractmethod(classmethod)
    def get_grating(self) -> float:
        raise NotImplementedError()

    @abc.abstractmethod(classmethod)
    def set_grating(self, grating: Any):
        raise NotImplementedError()

    @abc.abstractmethod(classmethod)
    def get_center_wavelength(self) -> float:
        raise NotImplementedError()

    @abc.abstractmethod(classmethod)
    def set_center_wavelength(self, wavelength: float):
        raise NotImplementedError()

    def __del__(self):
        self.close()


class SpectrometerDetector(abc.ABC):

    @abc.abstractmethod(classmethod)
    def init(self):
        raise NotImplementedError()

    @abc.abstractmethod(classmethod)
    def close(self):
        raise NotImplementedError()

    @abc.abstractmethod(classmethod)
    def get_temperature(self) -> float:
        raise NotImplementedError()

    @abc.abstractmethod(classmethod)
    def set_temperature(self, temperature: float):
        raise NotImplementedError()

    @abc.abstractmethod(classmethod)
    def get_exposure_time(self) -> float:
        raise NotImplementedError()

    @abc.abstractmethod(classmethod)
    def set_exposure_time(self, exposure_time: float):
        raise NotImplementedError()

    @abc.abstractmethod(classmethod)
    def acquire_single_frame(self, *args):
        raise NotImplementedError()

    @abc.abstractmethod(classmethod)
    def acquire_kinetic_series(self, *args):
        raise NotImplementedError()

    @abc.abstractmethod(classmethod)
    def acquire_step_and_glue(self, *args):
        raise NotImplementedError()

    def __del__(self):
        self.close()


class Spectrometer(abc.ABC):

    def __init__(
            self,
            diffraction_controller: DiffractionController,
            detector: SpectrometerDetector,
    ):
        self.diffraction_controller = diffraction_controller
        self.detector = detector

    def init(self):
        self.diffraction_controller.init()
        self.detector.init()

    def close(self):
        self.detector.close()
        self.diffraction_controller.close()

    def __del__(self):
        self.close()
