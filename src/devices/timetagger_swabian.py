"""
SwabianInstruments TimeTagger 20

Note: The TimeTagger Software has to be installed on the PC first for this class to work
Website: https://www.swabianinstruments.com/time-tagger/
"""


import sys
import logging
import subprocess

try:
    # DO NOT IMPORT WITH PIP
    # download and install TimeTagger software from SwabianInstruments website and inherit global python packages when
    # creating new virtual environment
    import TimeTagger
except ModuleNotFoundError:
    logging.critical("Could not load TimeTagger Module. Is the Time Tagger Software installed?")


class SwabianTimeTagger:
    """
    TimeTagger Series by Swabian Instruments
    """

    def __init__(self, name, address, settings):
        self.name = name
        self.address = address
        self.settings = settings

        # Connect
        try:
            self._ser = TimeTagger.createTimeTagger()
        except NameError:
            raise ConnectionError

        # Channel Names
        self.digital_channel = ["1", "2", "3", "4", "5", "6", "7", "8"]
        if "Digital Channel" in self.settings:
            for name, value in self.settings["Digital Channel"].items():
                self.digital_channel[name-1] = value

    def get_channel_int(self, channel):
        """
        Get Channel Number from String or Integer
        :param int | str channel: Channel Name
        """
        if isinstance(channel, str):
            return self.digital_channel.index(channel) + 1
        return channel

    def disconnect(self):
        """
        Disconnect from Device
        """
        self.reset()

    def reset(self):
        """
        Reset
        """
        self._ser.reset()

    def synchronize(self):
        """
        Synchronize
        """
        self._ser.sync()

    def set_clock_channel(self, channel, frequency=125_000, averaging=1000, wait_until_locked=True):
        """
        Set Software Clock
        :param int channel: Channel 1 to 8
        :param float frequency: Clock Frequency
        :param int averaging: Average over Number of Periods
        :param bool wait_until_locked: Wait until Software is locked to Clock Signal
        """
        self._ser.setSoftwareClock(input_channel=channel, input_frequency=frequency, averaging_periods=averaging,
                                   wait_until_locked=wait_until_locked)

    def get_counter(self, channel, bin_width, n_values):
        """
        Get Counter Object
        :param int | str channel: Channel
        :param float bin_width: Bin Width in s
        :param int n_values: Number of Bins
        :return: TimeTagger.Counter
        """
        channel_vec = TimeTagger.IntVector()
        channel_vec.append(self.get_channel_int(channel))
        bin_width = int(bin_width*1E12)     # convert to ps
        return TimeTagger.Counter(tagger=self._ser, channels=channel_vec, binwidth=bin_width, n_values=n_values)

    def get_count_rate(self, channel):
        """
        Get Count Rate
        :param int channel: Channel 1 to 8
        """
        channel_vec = TimeTagger.IntVector()
        channel_vec.append(self.get_channel_int(channel))
        return TimeTagger.Countrate(tagger=self._ser, channels=channel_vec)

    def get_histogram(self, click_channel, start_channel=1, bin_width=500E-12, n_bins=1000, delay=0):
        """
        Get Histogram
        :param int | str click_channel: Click count Channel 1 to 8
        :param int | str start_channel: Trigger Channel 1 to 8
        :param float bin_width: Bin Width in s
        :param float n_bins: Number of Bins
        :param float delay: Delay added to Click Channel
        :return: TimeTagger.Histogram
        """
        click_channel = self.get_channel_int(click_channel)
        start_channel = self.get_channel_int(start_channel)
        bin_width = int(bin_width*1E12)  # convert to ps
        n_bins = int(n_bins)

        if delay == 0:
            histogram = TimeTagger.Histogram(
                tagger=self._ser,
                click_channel=click_channel,
                start_channel=start_channel,
                binwidth=bin_width,
                n_bins=int(n_bins)
            )

        else:
            t0_channel = 1
            t0_delayed = TimeTagger.DelayedChannel(tagger=self._ser, input_channel=t0_channel, delay=delay)
            histogram = TimeTagger.Histogram(
                tagger=self._ser,
                click_channel=click_channel,
                start_channel=t0_delayed.getChannel(),
                binwidth=bin_width,
                n_bins=int(n_bins)
            )

        return histogram

    def gui_open(self):
        """
        Open Web GUI
        """
        if sys.platform == "linux":
            subprocess.Popen("timetagger", stdout=open('/dev/null', 'w'), stderr=open('/dev/null', 'w'))
        else:
            logging.error(f"{self.name}: Could not open GUI. Only supported on Linux.")
