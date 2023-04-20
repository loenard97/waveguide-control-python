from src.devices.main_device import EthernetDevice


class OscilloscopeKeysight(EthernetDevice):
    NAME = "Keysight 1200X Series Oscilloscope"
    ICON = "osci"

    def get_identity(self):
        return self.read("*IDN?")

    def measure_frequency(self, channel: int) -> str:
        return self.read(f"MEASure:FREQuency? CHANnel{channel}")

    def measure_volt_amplitude(self, channel: int) -> str:
        return self.read(f"MEASure:VAMPlitude? CHANnel{channel}")

    def measure_volt_maximum(self, channel: int) -> str:
        return self.read(f"MEASure:VMAX? CHANnel{channel}")

    def measure_volt_minimum(self, channel: int) -> str:
        return self.read(f"MEASure:VMIN? CHANnel{channel}")

    def measure_volt_peak_peak(self, channel: int) -> str:
        return self.read(f"MEASure:VPP? CHANnel{channel}")

    def gui_open(self):
        pass
