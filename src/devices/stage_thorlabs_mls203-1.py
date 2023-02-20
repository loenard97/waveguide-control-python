import re

from src.devices.device_main import USBDevice
from src.static_functions.wait import wait_msec


class ThorlabsStage(USBDevice):
    NAME = "Thorlabs MLS203-1 xy-Stage"
    ICON = "stage"
    TERMINATION_WRITE = '\r\n'
    TERMINATION_READ = 2
    BAUDRATE = 57600

    def __init__(self, address):
        USBDevice.__init__(self, address)
        self.velocity = 1

    def __repr__(self):
        """
        Return current state
        """
        return f"{self.NAME} at {self.address}\n" \
               f"Position: {self.get_position()}"

    def wait_until_ready(self):
        """
        Block until Stage is Ready
        """
        while self.get_position() == (-1, -1):
            wait_msec(200)

    def home_to_zero(self, direction):
        """
        Home to Zero Position
        """
        if direction == 'x':
            self.write("HX")
        elif direction == 'y':
            self.write("HY")
        else:
            raise ValueError("direction has to be 'x' or 'y'")

    def get_position(self):
        """
        returns tuple (x, y) of current position
        """
        out = self.read("S")
        if out == '':
            return -1, -1

        regex = r"^x(?P<x>.+)y(?P<y>.+)$"
        pattern = re.search(regex, out[:-1])

        return float(pattern.group(1)), float(pattern.group(2))

    def move_absolute(self, x, y, velocity=None, blocking=True):
        """
        Move Stage to Absolute Position
        """
        if velocity is None:
            velocity = self.velocity

        self.write(f"AX{x} Y{y} V{velocity}")
        if blocking:
            self.wait_until_ready()

    def move_relative(self, x, y, velocity=None, blocking=True):
        """
        Move Stage by Relative Distance
        """
        if velocity is None:
            velocity = self.velocity

        cur_x, cur_y = self.get_position()
        new_pos_x, new_pos_y = cur_x + x, cur_y + y

        self.write(f"AX{new_pos_x} Y{new_pos_y} V{velocity}")
        if blocking:
            self.wait_until_ready()
