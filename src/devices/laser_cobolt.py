from src.devices.main_device import USBDevice
from src.measurement.units import mA


class LaserCobolt(USBDevice):

    # Always returns 'OK', 'Syntax error: illegal command' or a value.
    # That means you should always use self.read("<command>") instead of self.write("<command>")

    TERMINATION_WRITE = '\r'
    BAUDRATE = 112500

    OPERATING_MODE_CODES = {
        "0": "Off",
        "1": "Waiting for key",
        "2": "Continuous",
        "3": "On/Off Modulation",
        "4": "Modulation",
        "5": "Fault",
        "6": "Aborted",

    }
    INTERLOCK_STATE_CODES = {
        "0": "OK",
        "1": "interlock open",
    }
    OPERATING_FAULT_CODES = {
        "0": "no errors",
        "1": "temperature error",
        "3": "interlock error",
        "4": "constant power timeout",
    }

    def get_error(self) -> None | str:
        return None

    def reset(self):
        self.clear_fault()

    def get_serial_number(self):
        """
        Get Serial Number
        """
        return self.read("gsn?")

    def set_output(self, state=False, force=False):
        """
        Set Laser Output
        :param bool state: Output State
        :param bool force: Force auto start
        """
        self.read(f"{'@cob' if force else '|'}{'1' if state else '2'}")

    def get_output(self):
        """
        Get Laser Output State
        """
        return '1' in self.read("l?")

    def get_key_state(self):
        """
        Get Key Switch State
        """
        return '1' in self.read("@cobasks?")

    def set_direct_input(self, state=False):
        """
        Set 5V Direct Input (OEM only)
        """
        self.read(f"@cobasdr{'1' if state else '2'}")

    def set_power(self, power=0.0):
        """
        Set Constant Power
        :param float power: Output Power in W
        """
        self.read("cp")
        self.read(f"p {power}")

    def get_power(self):
        """
        Get Current Power
        """
        return self.read("pa?")

    def set_mode_cw(self, power=0.0):
        """
        Set Constant Power Mode
        :param float power: Output Power in W
        """
        self.read("cp")
        self.read(f"p{power}")

    def set_mode_ci(self, current=0.0):
        """
        Set Constant Current Mode
        :param float current: Diode Current in A
        """
        self.read("ci")
        self.read(f"slc{current*mA}")

    def set_modulation_analog(self, power=0.0, state=True):
        """
        Set Digital Modulation
        :param float power: Output Power in W
        :param bool state: Modulation State
        """
        self.read("em")
        self.read("sdmes 0")
        self.set_power(power)
        self.read(f"sames {'1' if state else '0'}")

    def set_modulation_digital(self, power=0.0, state=True):
        """
        Set Digital Modulation
        :param float power: Output Power in W
        :param bool state: Modulation State
        """
        self.read("em")
        self.read("sames 0")
        self.set_power(power)
        self.read(f"sdmes {'1' if state else '0'}")

    def get_operating_mode(self):
        """
        Get Operation Mode
        """
        mode = self.read("gom?")
        return self.OPERATING_MODE_CODES[mode]

    def get_interlock_state(self):
        """
        Get Interlock state
        """
        state = self.read("ilk?")
        return self.INTERLOCK_STATE_CODES[state]

    def get_operating_fault(self):
        """
        Get operating fault
        """
        fault = self.read("f?")
        return self.OPERATING_FAULT_CODES[fault]

    def clear_fault(self):
        """
        Clear Faults
        """
        self.read("cf")

    def get_diode_operating_hours(self):
        """
        Get Diode Operating Hours
        """
        return self.read("hrs?")

    def get_analog_modulation_state(self):
        """
        Get Analog Modulation State
        """
        return self.read("games?")

    def set_modulation_mode(self):
        """
        enter modulation mode
        """
        self.read("em")

    def get_laser_current(self):
        """
        read actual laser current
        """
        return self.read("rlc?")

    def get_laser_current_set_point(self):
        """
        get laser current set point
        """
        return self.read("glc?")

    def get_output_power_set_point(self):
        """
        get output power set point
        """
        return self.read("p?")

    def set_laser_current(self, current):
        """
        set laser current
        :param Float current: laser current in mA
        """
        raise NotImplementedError

    # DPL specific Commands

    def set_modulation_high_current(self, current):
        """
        set modulation high current
        :param float current: current in mA
        """
        self.read(f"smc{current*mA}")

    def get_modulation_high_current(self):
        """
        get modulation high current
        """
        return self.read("gmc?")

    def set_modulation_low_current(self, current):
        """
        set modulation low current
        :param float current: current in mA
        """
        self.read(f"slth{current*mA}")

    def get_modulation_low_current(self):
        """
        get modulation low current
        """
        return self.read("glth?")

    def set_temperature(self, temperature):
        """
        set TEC_LDmod temperature
        :param float temperature: Temperature in °C
        """
        self.read(f"stec4t{temperature}")

    def get_temperature(self):
        """
        get TEC_LDmod set temperature
        """
        return self.read("gtec4t?")

    def get_actual_temperature(self):
        """
        read TEC_LDmod actual temperature
        """
        return self.read("rtec4t?")

    # MLD specific Commands

    def get_laser_modulation_power_set_point(self):
        """
        get laser modulation power set point
        """
        return self.read("glmp?")

    def set_laser_modulation_power(self, power):
        """
        set laser modulation power
        :param float power: power in mW
        """
        self.read(f"slmp{power}")

    def get_analog_low_impedance_state(self):
        """
        get analog low impedance state
        0: 1000 Ohm, 1: 50 Ohm
        """
        return self.read("galis?")

    def set_analog_low_impedance_state(self, state=True):
        """
        set analog low impedance state
        """
        self.read(f"salis{'1' if state else '0'}")
