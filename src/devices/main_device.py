import serial       # package name 'pyserial'
import pyvisa
import logging


class Device:
    """
    Device Interface
    """

    def __init__(self, name: str, address: str, settings=None):
        """
        Connect to Device
        :param str name: Name of Device
        :param str address: Address of Device
        :param dict settings: Dictionary of Settings
        """
        self._ser = None        # Serial Object handling the Communication
        self._app = None        # Qt Widget shown when open_gui() is called
        self.settings = settings if settings is not None else {}
        self.name = name
        self.address = address

    def disconnect(self) -> None:
        """
        Disconnect from Device
        """
        raise NotImplementedError

    def get_error(self) -> str:
        """
        Get Last Error from Device.
        :return str: Empty String if no Error occurred, otherwise Error Message
        :raises NotImplementedError:
        """
        raise NotImplementedError

    def reset(self) -> None:
        """
        Reset Device to default Settings
        """
        raise NotImplementedError

    def write(self, message: str = "", error_checking: bool = True) -> None:
        """
        Write Message to Device
        Each written message should be logged via logging.info(f"{self.name}: Send '{message}'")
        :param str message: Message to send
        :param bool error_checking: Check if Error occurred after writing
        :raises ConnectionError: Connection failed or Device Error occurred with the message
            "{self.name}: Could not write '{message}'. Error: '{err}'."
        """
        raise NotImplementedError

    def read(self, message: str = "", error_checking: bool = True) -> str:
        """
        Read Message from Device
        Each received message should be logged via logging.info(f"{self.name}: Recv '{message}'")
        :param str message: Message to query
        :param bool error_checking: Check if Error occurred after reading
        :return: Received Answer
        :raises ConnectionError: Connection failed or Device Error occurred with the message
            "{self.name}: Could not read '{message}'. Error: '{err}'."
        """
        raise NotImplementedError

    def open_gui(self) -> None:
        """
        Open GUI of Device
        """
        if self._app is None:
            logging.error(f"{self.name}: Could not open GUI. Method 'open_gui' is not defined.")


class USBDevice:
    """
    USB Device based on PySerial
    """

    # Default USB Settings
    TERMINATION_WRITE = ''
    TERMINATION_READ = 1
    BAUDRATE = 9600
    TIMEOUT = 2
    PARITY = serial.PARITY_NONE
    STOPBITS = serial.STOPBITS_ONE
    BYTESIZE = serial.EIGHTBITS

    def __init__(self, name="Unnamed Device", address="", settings=None):
        """
        Connect to Device
        :param str name: Name
        :param str address: COM Port on Windows, File Name on Linux
        """
        self._app = None        # Qt Widget shown when open_gui() is called
        self.settings = settings if settings is not None else {}
        self.name = name
        self.address = address
        try:
            self._ser = serial.Serial(self.address, baudrate=self.BAUDRATE, timeout=self.TIMEOUT, parity=self.PARITY,
                                      stopbits=self.STOPBITS, bytesize=self.BYTESIZE)
        except Exception as err:
            raise ConnectionError(f"{self.name}: Could not connect. Error '{err}'")
        if not self._ser.isOpen():
            self._ser.open()

    def disconnect(self) -> None:
        """
        Disconnect from Device
        """
        logging.info(f"{self.name}: Disconnect.")
        self._ser.close()

    def get_error(self) -> str:
        """
        Get Last Error from Device.
        :return str: Empty String if no Error occurred, otherwise Error Message
        :raises NotImplementedError:
        """
        raise NotImplementedError

    def reset(self) -> None:
        """
        Reset Device to default Settings
        """
        raise NotImplementedError

    def write(self, message: str = "", error_checking: bool = True) -> None:
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
            if error_checking:
                last_error = self.get_error()
                if last_error:
                    raise ConnectionError(f"{self.name}: Could not write '{message}'. Error: '{last_error}'.")
            logging.info(f"{self.name}: Send '{message}'.")

    def read(self, message: str = "", error_checking: bool = True) -> str:
        """
        Read Message from Device
        :param str message: Message to query
        :param bool error_checking: Check if Error occurred after reading
        :return: Received Answer
        :raises ConnectionError: Connection failed or Device Error occurred
        """
        self._ser.reset_input_buffer()
        self.write(message)
        try:
            ret = self._ser.readline().decode().strip()
        except Exception as err:
            raise ConnectionError(f"{self.name}: Could not read '{message}'. Error: '{err}'.")
        else:
            if error_checking:
                last_error = self.get_error()
                if last_error:
                    raise ConnectionError(f"{self.name}: Could not read '{message}'. Error: '{last_error}'.")
            logging.info(f"{self.name}: Recv '{ret}'.")
            return ret

    def open_gui(self) -> None:
        """
        Open GUI of Device
        """
        if self._app is None:
            logging.error(f"{self.name}: Could not open GUI. Method 'open_gui' is not defined.")


class EthernetDevice:
    """
    Ethernet Device based on PyVisa
    """

    # Default Ethernet Settings
    TERMINATION_WRITE = ''
    TERMINATION_READ = 1

    def __init__(self, name="Unnamed Device", address="", settings=None):
        """
        Connect to Device
        :param str name: Name
        :param str address: IP Address
        """
        self._app = None        # Qt Widget shown when open_gui() is called
        self.settings = settings if settings is not None else {}
        self.name = name
        self.address = address
        try:
            self._ser = pyvisa.ResourceManager().open_resource(f"TCPIP::{self.address}::INSTR")
            self._ser.open()
        except pyvisa.errors.VisaIOError as err:
            raise ConnectionError(f"{self.name}: Could not connect. Error: '{err}'.")

    def disconnect(self) -> None:
        """
        Disconnect from Device
        """
        logging.info(f"{self.name}: Disconnect.")
        self._ser.close()

    def get_error(self) -> str:
        """
        Get Last Error from Device.
        :return str: Empty String if no Error occurred, otherwise Error Message
        :raises NotImplementedError:
        """
        raise NotImplementedError

    def reset(self) -> None:
        """
        Reset Device to default Settings
        """
        raise NotImplementedError

    def write(self, message: str = "", error_checking: bool = True) -> None:
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
                error_msg = self.get_error()
                if error_msg:
                    raise ConnectionError(f"{self.name}: Could not write '{message}'. Error: '{error_msg}'.")
            logging.info(f"{self.name}: Send '{message}'.")

    def read(self, message: str = "", error_checking: bool = True) -> str:
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
            if error_checking:
                error_msg = self.get_error()
                if error_msg:
                    raise ConnectionError(f"{self.name}: Could not read '{message}'. Error: '{self.get_error()}'.")
            logging.info(f"{self.name}: Recv '{ret}'.")
            return ret

    def open_gui(self) -> None:
        """
        Open GUI of Device
        """
        if self._app is None:
            logging.error(f"{self.name}: Could not open GUI. Method 'open_gui' is not defined.")
