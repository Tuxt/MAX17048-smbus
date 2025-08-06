import struct
from typing import NoReturn, Optional, Type

from .typing import I2CDeviceDriver


class RWRegister:
    """
    Read-Write register.

    This class allows reading and writing to a specific register of an I2C device.
    """

    def __init__(self, register_address: int, struct_format: str) -> None:
        self.address = register_address
        self.format = struct_format
        self.size = struct.calcsize(struct_format)

    def __get__(self, obj: Optional[I2CDeviceDriver], objtype: Optional[Type[I2CDeviceDriver]] = None) -> int:
        """
        Read the current value from the register.

        Parameters
        ----------
        obj : I2CDeviceDriver
            Instance containing the `i2c_device` for communication.
        objtype : Type[I2CDeviceDriver], optional
            The type of the `obj` instance.

        Returns
        -------
        int
            Value read from the register.
        """
        data = obj.i2c_device.read(self.address, self.size)
        return struct.unpack(self.format, data)[0]

    def __set__(self, obj: I2CDeviceDriver, value: int) -> None:
        """
        Write a value to the register.

        Parameters
        ----------
        obj : I2CDeviceDriver
            Instance containing the `i2c_device` for communication.
        value : int
            Value to write to the register.
        """
        data = struct.pack(self.format, value)
        obj.i2c_device.write(self.address, data)


class RORegister(RWRegister):
    """
    Read-Only register.

    Inherits from RWRegister but does not allow writing.
    """

    def __set__(self, obj: I2CDeviceDriver, value: int) -> NoReturn:
        """
        Prevent writing to a read-only register.

        Parameters
        ----------
        obj : I2CDeviceDriver
            Instance containing this descriptor.
        value : int
            Value attempted to be written.

        Raises
        ------
        AttributeError
            Always raised to indicate the register is read-only.
        """
        raise AttributeError("Cannot write to read-only register")


class RWBit:
    """
    Read-Write bit in a register.

    This class allows reading and writing to a specific bit in a register of an I2C device.
    """

    def __init__(self, register_address: int, bit: int, register_byte: int = 1) -> None:
        # 16-bit word addressing
        if register_address % 2 != 0:
            raise ValueError("Register address must be even")

        if bit < 0 or bit > 7:
            raise ValueError("Bit must be between 0 and 7")
        if register_byte < 0 or register_byte > 2:
            raise ValueError("Register byte must be between 0 and 2")

        self.address = register_address
        self.bit_mask = 1 << bit
        self.byte = register_byte

    def __get__(self, obj: Optional[I2CDeviceDriver], objtype: Optional[Type[I2CDeviceDriver]] = None) -> bool:
        """
        Read the current value of the bit.

        Parameters
        ----------
        obj : I2CDeviceDriver
            Instance containing the `i2c_device` for communication.
        objtype : Type[I2CDeviceDriver], optional
            The type of the `obj` instance.

        Returns
        -------
        bool
            Current value of the bit (True or False).
        """
        data = obj.i2c_device.read(self.address, self.byte)
        return bool(data[self.byte] & self.bit_mask)

    def __set__(self, obj: I2CDeviceDriver, value: bool) -> None:
        """
        Write a value to the bit.

        Parameters
        ----------
        obj : I2CDeviceDriver
            Instance containing the `i2c_device` for communication.
        value : bool
            Value to write to the bit (True or False).
        """
        data = obj.i2c_device.read(self.address, self.byte)
        if value:
            data[self.byte] |= self.bit_mask
        else:
            data[self.byte] &= ~self.bit_mask
        obj.i2c_device.write(self.address, data)


class ROBit(RWBit):
    """
    Read-Only bit in a register.

    Inherits from RWBit but does not allow writing.
    """

    def __set__(self, obj: I2CDeviceDriver, value: bool) -> NoReturn:
        """
        Prevent writing to a read-only bit.

        Parameters
        ----------
        obj : I2CDeviceDriver
            Instance containing the `i2c_device` for communication.
        value : bool
            Value attempted to be written.

        Raises
        ------
        AttributeError
            Always raised to indicate the bit is read-only.
        """
        raise AttributeError("Cannot write to read-only bit")
