import struct
from typing import NoReturn, Optional, Type

from .typing import I2CDeviceDriver


class RWRegister:
    """
    Read-Write register.

    This class allows reading and writing to a specific register of an I2C device.
    """

    _READ_ONLY = False

    def __init__(self, register_address: int, struct_format: str) -> None:
        # 16-bit word alignment
        if not self._READ_ONLY and register_address % 2 != 0:
            raise ValueError("Register address must be even")
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

    _READ_ONLY = True

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

    _READ_ONLY = False

    def __init__(self, register_address: int, bit: int, register_byte: int = 1) -> None:
        # 16-bit word alignment
        if not self._READ_ONLY and register_address % 2 != 0:
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

    _READ_ONLY = True

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


class RWBitsUnsigned:
    """
    Read/Write unsigned bit field in a register.

    This class provides a way to read and write unsigned integer values
    from a specific bit field within a register of an I2C device. It is
    used as a descriptor to access the bit field value from an instance of
    a class that includes an I2C device interface.

    Attributes
    ----------
    _READ_ONLY : bool
        Indicates whether this register is read-only (True) or read-write (False).
    address : int
        The register address to read/write.
    mask : int
        Bit mask for the field.
    num_bits : int
        Number of bits in the field.
    lowest_bit : int
        Position of the least significant bit (0-based).
    size : int
        Size of the register in bytes.
    
    Methods
    -------
    __get__(self, obj: I2CDeviceDriver, objtype: Optional[Type[I2CDeviceDriver]] = None) -> int
        Read the current value from the bits.
    __set__(self, obj: I2CDeviceDriver, value: int) -> None
        Write a value to the bits.

    Notes
    -----
    The :attr:`_READ_ONLY` class attribute is set to ``False`` to indicate that
    the register is read-write. This does not allow for odd memory addresses to
    be used, since the address is modified by the write operation.

    See Also
    --------
    :class:`ROBitsUnsigned`
    """

    _READ_ONLY = False

    def __init__(self, register_address: int, num_bits: int, lowest_bit: int, register_width: int = 1) -> None:
        """
        Initialize the read/write unsigned bit field descriptor.

        Parameters
        ----------
        register_address : int
            The register address to read/write. Must be an even address.
        num_bits : int
            Number of bits in the bit field (must be positive).
        lowest_bit : int
            The position of the least significant bit (0-based).
        register_width : int, optional
            Size of the register in bytes, by default 1.

        Raises
        ------
        ValueError
            If `register_address` is not an even address.
        ValueError
            If `num_bits` is not positive.
        ValueError
            If `lowest_bit` is not non-negative.
        ValueError
            If `register_width` is not between 1 and 2.
        """
        # 16-bit word alignment
        if not self._READ_ONLY and register_address % 2 != 0:
            raise ValueError("Register address must be even")
        if num_bits <= 0:
            raise ValueError("Number of bits must be positive")
        if lowest_bit < 0:
            raise ValueError("Lowest bit must be non-negative")
        if register_width < 1 or register_width > 2:
            raise ValueError("Register width must be between 1 and 2")
        self.address = register_address
        self.mask = ((1 << num_bits) - 1) << lowest_bit
        self.num_bits = num_bits
        self.lowest_bit = lowest_bit
        self.size = register_width

    def __get__(self, obj: I2CDeviceDriver, objtype: Optional[Type[I2CDeviceDriver]] = None) -> int:
        """
        Read the current value from the bits.

        Parameters
        ----------
        obj : I2CDeviceDriver
            Instance containing the `i2c_device` for communication.
        objtype : Optional[Type[I2CDeviceDriver]], optional
            The type of the `obj` instance.

        Returns
        -------
        int
            Value read from the bits.
        """
        data = obj.i2c_device.read(self.address, self.size)
        reg = 0
        for byte in data:
            reg = (reg << 8) | byte
        return (reg & self.mask) >> self.lowest_bit

    def __set__(self, obj: I2CDeviceDriver, value: int) -> None:
        """
        Write a value to the bits.

        Parameters
        ----------
        obj : I2CDeviceDriver
            Instance containing the `i2c_device` for communication.
        value : int
            Value to write to the bits.

        Raises
        ------
        ValueError
            If `value` is out of range for the bit field.
        """
        if value < 0 or value >= (1 << self.num_bits):
            raise ValueError(f"Value {value} out of range for {self.num_bits} bits")

        data = obj.i2c_device.read(self.address, self.size)
        reg = 0
        for byte in data:
            reg = (reg << 8) | byte
        reg &= ~self.mask
        reg |= value << self.lowest_bit
        data = []
        for _ in range(self.size):
            data.append(reg & 0xFF)
            reg >>= 8
        obj.i2c_device.write(self.address, reversed(data))


class ROBitsUnsigned(RWBitsUnsigned):
    """
    Read-Only unsigned bit field in a register.

    This class allows accessing specific bit fields within a register
    as if they were individual values, handling all the bit manipulation
    internally. It's designed for unsigned integer values.

    Attributes
    ----------
    _READ_ONLY : bool
        Indicates whether this register is read-only (True) or read-write (False).
    address : int
        The register address to read.
    mask : int
        Bit mask for the field.
    num_bits : int
        Number of bits in the field.
    lowest_bit : int
        Position of the least significant bit (0-based).
    size : int
        Size of the register in bytes.

    Notes
    -----
    The :attr:`_READ_ONLY` class attribute is set to ``True`` to indicate that
    the register is read-only. This allows for odd memory addresses to be used,
    since the address is not modified by the write operation.

    """

    _READ_ONLY = True

    def __set__(self, obj: I2CDeviceDriver, value: int) -> NoReturn:
        """
        Prevent writing to a read-only bit field.

        Parameters
        ----------
        obj : I2CDeviceDriver
            Instance containing the `i2c_device` for communication.
        value : int
            Value attempted to be written.

        Raises
        ------
        AttributeError
            Always raised to indicate the bit field is read-only.
        """
        raise AttributeError("Cannot write to read-only bit field")
