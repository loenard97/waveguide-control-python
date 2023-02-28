import numpy as np
from dataclasses import dataclass

from src.measurement.units import *


class Sequence:
    """
    Manage one Sequence of Pulses
    """

    def __init__(self, pulse_sequence):
        self.sequence = pulse_sequence
        self.length = 0     # in ns for precision
        for pulse in self.sequence:
            self.length += int(pulse.length * 1E9)

    def get_sequence_list(self, n_samples=5000) -> np.array:
        """
        Return Sequence as Array
        """
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
        ret_sequence = []
        for pulse in self.sequence:
            if isinstance(pulse, High):
                ret_sequence.append((int(pulse.length*1E9), 1))
            elif isinstance(pulse, Low):
                ret_sequence.append((int(pulse.length*1E9), 0))
            else:
                raise ValueError("Unknown Pulse Shape")
        return ret_sequence

    def get_sequence_keysight_awg(self, n_samples=1000) -> (str, int):
        """
        Return Sequence in Keysight AWG Format
        :returns (str, int): Sequence as String and Number of Samples per seconds
        """
        # Always subject to floating point rounding errors, but final sequence should at most be only one Sample
        # shorter than intended
        ret = ""
        sample_rate = int(n_samples/self.length*1E9)   # floored samples per s
        for pulse in self.sequence:
            if isinstance(pulse, High):
                ret += "1, " * int(pulse.length * sample_rate)
            elif isinstance(pulse, Low):
                ret += "0, " * int(pulse.length * sample_rate)
            else:
                raise ValueError("Unknown Pulse Shape")
        return ret[:-2], sample_rate


class On:
    """
    Pulse Sequence that is always High
    """

    @classmethod
    def get_sequence_pulse_streamer(cls):
        """
        Return Sequence in Pulse Streamer Format
        """
        return [(1E3, 1)]


class Off:
    """
    Pulse Sequence that is always Low
    """

    @classmethod
    def get_sequence_pulse_streamer(cls):
        """
        Return Sequence in Pulse Streamer Format
        """
        return [(1E3, 0)]


class Trigger:
    """
    Pulse Sequence for one Trigger Pulse
    """

    @classmethod
    def get_sequence_pulse_streamer(cls):
        """
        Return Sequence in Pulse Streamer Format
        """
        return [(1E3, 1), (1E3, 0)]


@dataclass(repr=True, frozen=True)
class High:
    """
    Rectangle Pulse with Level 1
    """
    length: float


@dataclass(repr=True, frozen=True)
class Low:
    """
    Rectangle Pulse with Level 0
    """
    length: float
