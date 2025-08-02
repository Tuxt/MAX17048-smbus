from .smbus import SMBus


class I2CDevice:
    def __init__(self, i2c_bus: int, address: int, probe: bool = True) -> None:
        self.bus = SMBus(i2c_bus)
        self.device_address = address

        if probe:
            self.__probe_for_device()

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
