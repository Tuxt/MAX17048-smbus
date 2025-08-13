"""
I²C device communication interface.

This module provides the ``I2CDevice`` class, which abstracts the underlying
I²C backend to offer a consistent interface for reading from and writing to
a device at a given bus and address. It is intended both for direct low-level
transactions and as a base for higher-level device drivers.

Examples
--------
Instantiate the I²C device on bus 1 at address 0x36, and read 1 byte from register 0x04:

>>> from i2c_device import I2CDevice
>>> dev = I2CDevice(1, 0x36)
>>> data = dev.read(0x04)
"""

from .smbus import SMBus


class I2CDevice:
    """
    Thin abstraction layer for accessing an I²C device via an SMBus-compatible backend.

    This class wraps an ``SMBus``-compatible instance to provide an interface for reading
    from and writing to a specific I²C device address. It handles device addressing and
    delegates the actual bus operations to the underlying backend, allowing higher-level
    drivers to remain agnostic of the specific SMBus implementation in use.

    Attributes
    ----------
    bus : SMBus
        The internally managed ``SMBus`` instance used for I²C communication.
    device_address : int
        The 7-bit I²C address of the device.

    Methods
    -------
    read(register: int, length: int = 1) -> bytes
        Read bytes from the device starting at the given register.
    write(register: int, data: bytes) -> None
        Write bytes to the device starting at the given register.
    """

    def __init__(self, i2c_bus: int, address: int, probe: bool = True) -> None:
        """
        Initialize an I²C device interface.

        Parameters
        ----------
        i2c_bus : int
            I²C bus number to open. An ``SMBus`` instance will be created internally
            for this bus.
        address : int
            7-bit I²C address of the target device.
        probe : bool, optional
            If ``True`` (default), the device will be probed after initialization
            to verify its presence.
        """
        self.bus = SMBus(i2c_bus)
        self.device_address = address

        if probe:
            self.__probe_for_device()

    def read(self, register: int, length: int = 1) -> bytes:
        """
        Read one or two bytes from the device starting at the given register.

        This method reads from the I²C device to retrieve raw data from the
        specified register address. The number of bytes to read is limited to
        ``1`` or ``2``.

        Parameters
        ----------
        register : int
            Register address to read from.
        length : int, optional
            Number of bytes to read. Must be ``1`` or ``2`` (default is ``1``).

        Returns
        -------
        bytes
            Data read from the device.

        Raises
        ------
        :py:exc:`ValueError`
            If ``length`` is not ``1`` or ``2``.
        """
        if length not in (1, 2):
            raise ValueError("Length must be 1 or 2.")
        return bytes(self.bus.read_i2c_block_data(self.device_address, register, length))

    def write(self, register: int, data: bytes) -> None:
        """
        Write one or two bytes to the I²C device starting at the given register.

        This method writes to the I²C device to store raw data at the
        specified register address. The number of bytes to write is limited to
        ``1`` or ``2``.

        Parameters
        ----------
        register : int
            Register address to write to.
        data : bytes
            Bytes to write to the device. Must be ``1`` or ``2`` bytes.

        Raises
        ------
        :py:exc:`ValueError`
            If ``data`` is not ``1`` or ``2`` bytes.
        """
        if len(data) not in (1, 2):
            raise ValueError("Data must be 1 or 2 bytes.")
        self.bus.write_i2c_block_data(self.device_address, register, list(data))

    def __probe_for_device(self) -> None:
        """
        Verify that the device responds at the configured I²C address.

        This method performs a minimal probe by attempting to read a single byte
        from the device. If there is no acknowledgement or the device is busy,
        the operation fails and an exception is raised.

        Raises
        ------
        :py:exc:`ConnectionError`
            If the device does not respond at the specified address.
        """
        try:
            self.bus.read_byte(self.device_address)
        except OSError as e:
            self.bus.close()
            raise ConnectionError(
                f"Device at address {self.device_address:#04x} not found on I2C bus {self.bus.bus_number}."
            ) from e
