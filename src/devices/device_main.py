import serial       # package name 'pyserial'
import pyvisa
import logging


class USBDevice:
    """
    USB Device based on pyserial
    """

    # Default USB Settings
    TERMINATION_WRITE = ''
    TERMINATION_READ = 1
    BAUDRATE = 9600
    TIMEOUT = 2
    PARITY = serial.PARITY_NONE
    STOPBITS = serial.STOPBITS_ONE
    BYTESIZE = serial.EIGHTBITS

    def __init__(self, name, address, settings):
        """
        Connect to Device
        :param str name: Name
        :param str address: COM Port on Windows, File Name on Linux
        """
        self.name = name
        self.address = address
        self.settings = settings
        self.app = None
        try:
            self._ser = serial.Serial(self.address, baudrate=self.BAUDRATE, timeout=self.TIMEOUT, parity=self.PARITY,
                                      stopbits=self.STOPBITS, bytesize=self.BYTESIZE)
        except Exception as err:
            raise ConnectionError(f"{self.name}: Could not connect. Error '{err}'")
        if not self._ser.isOpen():
            self._ser.open()

    def disconnect(self):
        """
        Disconnect from Device
        """
        self._ser.close()

    def get_error(self) -> None | str:
        """
        Get Last Error from Device.
        Every Device Class has to implement this individually
        :return None | str: None if no Error occurred, otherwise str with Error Message
        :raises NotImplementedError:
        """
        raise NotImplementedError(f"{self.name}: Function 'get_error()' is not implemented for this device.")

    def write(self, message: str, error_checking=True):
        """
        Write Message to Device
        :param str message: Message to send
        :param bool error_checking: Check if Error occurred after writing
        :raises ConnectionError: Connection failed or Device Error occurred
        """
        try:
            self._ser.write((message+self.TERMINATION_WRITE).encode())
        except pyvisa.errors.VisaIOError as err:
            raise ConnectionError(f"{self.name}: Could not write '{message}'. Error: '{err}'.")
        else:
            if error_checking and self.get_error() is not None:
                raise ConnectionError(f"{self.name}: Could not write '{message}'. Error: '{self.get_error()}'.")
            logging.info(f"{self.name}: Send '{message}'")

    def read(self, message: str, error_checking=True) -> str:
        """
        Read Message from Device
        :param str message: Message to query
        :param bool error_checking: Check if Error occurred after reading
        :return: Received Answer
        :raises ConnectionError: Connection failed or Device Error occurred
        """
        self.write(message)
        try:
            ret = self._ser.readline().decode()[:-self.TERMINATION_READ]
        except Exception as err:
            raise ConnectionError(f"{self.name}: Could not read '{message}'. Error: '{err}'.")
        else:
            if error_checking and self.get_error() is not None:
                raise ConnectionError(f"{self.name}: Could not read '{message}'. Error: '{self.get_error()}'.")
            logging.info(f"{self.name}: Recv '{ret}'")
            return ret


class EthernetDevice:
    """
    Ethernet Device based on PyVisa
    """

    # Default Ethernet Settings
    TERMINATION_WRITE = ''
    TERMINATION_READ = 1

    def __init__(self, name="Unnamed Ethernet Device", address="", settings=None):
        """
        Connect to Device
        :param str name: Name
        :param str address: IP Address
        """
        self.name = name
        self.address = address
        self.settings = settings
        self.app = None
        try:
            self._ser = pyvisa.ResourceManager().open_resource(f"TCPIP::{self.address}::INSTR")
            self._ser.open()
        except pyvisa.errors.VisaIOError as err:
            raise ConnectionError(f"{self.name}: Could not connect. Error: '{err}'")

    def disconnect(self):
        """
        Disconnect from Device
        """
        self._ser.close()

    def get_error(self) -> None | str:
        """
        Get Last Error from Device.
        Every Device Class has to implement this individually
        :return None | str: None if no Error occurred, otherwise str with Error Message
        :raises NotImplementedError:
        """
        raise NotImplementedError(f"{self.name}: Function 'get_error()' is not implemented for this device.")

    def write(self, message: str, error_checking=True):
        """
        Write Message to Device
        :param str message: Message to send
        :param bool error_checking: Check if Error occurred after writing
        :raises ConnectionError: Connection failed or Device Error occurred
        """
        try:
            self._ser.write(message+self.TERMINATION_WRITE)    # NOQA
        except pyvisa.errors.VisaIOError as err:
            raise ConnectionError(f"{self.name}: Could not write '{message}'. Error: '{err}'.")
        else:
            if error_checking:
                err = self.get_error()
                if err:
                    raise ConnectionError(f"{self.name}: Could not write '{message}'. Error: '{err}'.")
            logging.info(f"{self.name}: Send '{message}'")

    def read(self, message: str, error_checking=True) -> str:
        """
        Read Message from Device
        :param str message: Message to query
        :param bool error_checking: Check if Error occurred after reading
        :return: Received Answer
        :raises ConnectionError: Connection failed or Device Error occurred
        """
        try:
            ret = self._ser.query(message)[:-self.TERMINATION_READ]  # NOQA
        except pyvisa.errors.VisaIOError as err:
            raise ConnectionError(f"{self.name}: Could not read '{message}'. Error: '{err}'.")
        else:
            if error_checking and self.get_error() is not None:
                raise ConnectionError(f"{self.name}: Could not read '{message}'. Error: '{self.get_error()}'.")
            logging.info(f"{self.name}: Recv '{ret}'")
            return ret
