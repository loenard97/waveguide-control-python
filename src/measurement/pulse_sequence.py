import numpy as np
from dataclasses import dataclass

from src.measurement.units import us


class Sequence:
    """
    Manage one Sequence of Pulses
    """
    # The methods that return the sequence as a list for each device are always subject to floating point rounding
    # errors, but the final sequence should at most be only one sample shorter than intended.
    # So far I never had any problems with that. If that gets problematic at some point, maybe try to use the decimal
    # library instead: https://docs.python.org/3/library/decimal.html

    def __init__(self, pulse_sequence):
        self.sequence = pulse_sequence
        self.length = 0     # in ns for precision
        for pulse in self.sequence:
            self.length += int(pulse.length * 1E9)

    def get_sequence_list(self, n_samples=5000):
        """
        Return Sequence as Array
        """
        # Return sequence as numpy array for plotting purposes

        ret = np.array([])
        sample_rate = int(n_samples / self.length * 1E9)  # floored samples per s
        for pulse in self.sequence:
            if isinstance(pulse, High):
                ret = np.append(ret, np.ones(int(pulse.length * sample_rate)))
            elif isinstance(pulse, Low):
                ret = np.append(ret, np.zeros(int(pulse.length * sample_rate)))
            else:
                raise ValueError("Unknown Pulse Shape")
        ret = np.append(ret, np.zeros(n_samples - len(ret)))
        return ret

    def get_sequence_pulse_streamer(self) -> list:
        """
        Return Sequence in Pulse Streamer Format
        """
        # PulseStreamer format is a list of tuples per pulse with length in ns and level:
        # [(100, 0), (500, 1)] equals 100ns nothing, then 500ns pulse.
        # Digital Outputs only allow 0 or 1 as level.

        ret_sequence = []
        for pulse in self.sequence:
            if isinstance(pulse, High):
                ret_sequence.append((int(pulse.length*1E9), 1))
            elif isinstance(pulse, Low):
                ret_sequence.append((int(pulse.length*1E9), 0))
            else:
                raise ValueError("Unknown Pulse Shape")
        return ret_sequence

    def get_sequence_keysight_awg(self, sample_rate) -> str:
        """
        Return Sequence in Keysight AWG Format
        :param float sample_rate: Sample Rate in Samples per Second
        """
        # Keysight AWG format is one string with values from 0 to 1 like this:
        # "0, 0, 0, 0.1, 0.5, 0.6, 1, 1, 1, 0, 0, 0"
        # This string has to have a minimal length that is not checked for here, because it usually isn't problematic

        return ', '.join(
            [f"{pulse.level:.4f}" for pulse in self.sequence for _ in range(int(pulse.length*sample_rate))])


@dataclass
class On:
    """
    Pulse Sequence that is always High
    """
    level: float = 1.0
    length: float = 1*us

    def get_sequence_pulse_streamer(self):
        """
        Return Sequence in Pulse Streamer Format
        """
        return [(int(self.length*1E9), 1)]


@dataclass
class Off:
    """
    Pulse Sequence that is always Low
    """
    level: float = 0.0
    length: float = 1*us

    def get_sequence_pulse_streamer(self):
        """
        Return Sequence in Pulse Streamer Format
        """
        return [(int(self.length*1E9), 0)]


@dataclass
class Trigger:
    """
    Pulse Sequence for one Trigger Pulse
    """
    level: float = 1.0
    length: float = 1*us
    offset: float = 0.0

    def get_sequence_pulse_streamer(self):
        """
        Return Sequence in Pulse Streamer Format
        """
        return [(int(self.offset*1E9), 0), (int(self.length*1E9), 1), (1E2, 0)]


@dataclass
class High:
    """
    Rectangle Pulse with Level 1
    """
    length: float = 1*us
    level: float = 1.0


@dataclass
class Low:
    """
    Rectangle Pulse with Level 0
    """
    length: float = 1*us
    level: float = 0.0
