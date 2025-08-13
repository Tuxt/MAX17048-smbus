from .smbus import SMBus


class I2CDevice:
    def __init__(self, i2c_bus: int, address: int, probe: bool = True) -> None:
        self.bus = SMBus(i2c_bus)
        self.device_address = address

        if probe:
            self.__probe_for_device()

    def read(self, register: int, length: int = 1) -> bytes:
        """
        Read bytes from the device at the specified register.

        Parameters
        ----------
        register : int
            Register address to read from.
        length : int, optional
            Number of bytes to read. Must be ``1`` or ``2`` (default is ``1``).

        Returns
        -------
        bytes
            The data read from the device.
        """
        if length not in (1, 2):
            raise ValueError("Length must be 1 or 2.")
        return bytes(self.bus.read_i2c_block_data(self.device_address, register, length))

    def write(self, register: int, data: bytes) -> None:
        """
        Write bytes to the device at the specified register.

        Parameters
        ----------
        register : int
            Register address to write to.
        data : bytes
            Bytes to write to the device. Must be ``1`` or ``2`` bytes.
        """
        if len(data) not in (1, 2):
            raise ValueError("Data must be 1 or 2 bytes.")
        self.bus.write_i2c_block_data(self.device_address, register, list(data))

    def __probe_for_device(self) -> None:
        """
        Check whether the device is present and responsive at the configured I2C address.

        The method performs a simple probe by attempting to read a byte from the device.
        If the device does not respond or is busy, a ConnectionError is raised.

        Raises
        ------
            ConnectionError: If the device is not found at the specified address.
        """
        try:
            self.bus.read_byte(self.device_address)
        except OSError as e:
            self.bus.close()
            raise ConnectionError(
                f"Device at address {self.device_address:#04x} not found on I2C bus {self.bus.bus_number}."
            ) from e
