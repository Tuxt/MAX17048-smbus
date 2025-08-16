"""
Registers and bits within registers of an I2C device.

Provides classes for representing registers and bits within registers of an I2C
device.
"""

import struct
from typing import NoReturn, Optional, Type

from .typing import I2CDeviceDriver


class RegisterField:
    def __init__(
        self,
        register_address: int,
        num_bits: int,
        lowest_bit: int = 0,
        signed: bool = False,
        independent_bytes: bool = False,
    ) -> None:
        field_span = lowest_bit + num_bits

        # INPUT VALIDATION
        # Register address must be even (2 bytes): Some registers require writing 2 bytes
        if register_address % 2:
            raise ValueError(f"Register address must be even, got {register_address}")
        if not (0 < num_bits <= 16):
            raise ValueError(f"Invalid num_bits {num_bits}, must be in range 1-16")
        if not (0 <= lowest_bit < 16):
            raise ValueError(f"Invalid lowest_bit {lowest_bit}, must be in range 0-15")
        # The offset and size can't exceed 16 bits
        if field_span > 16:
            raise ValueError(f"Invalid field size: lowest_bit ({lowest_bit}) + num_bits ({num_bits}) exceeds 16 bits")

        # DATA CALCULATION
        self.address = (
            register_address + 1 if independent_bytes and lowest_bit < 8 and field_span <= 8 else register_address
        )
        self.size = 2 if not independent_bytes or (lowest_bit < 8 and field_span > 8) else 1
        self.num_bits = num_bits
        self.lowest_bit = lowest_bit
        self.mask = ((1 << num_bits) - 1) << lowest_bit  # 16-bit mask (it's already 8-bit if LSB)
        if self.size == 1 and lowest_bit >= 8:
            self.mask >>= 8  # 8-bit mask (if only one byte and it's MSB)
        self.signed = signed

    def __get__(self, obj: I2CDeviceDriver, objtype: Optional[Type[I2CDeviceDriver]] = None) -> int:
        data = obj.i2c_device.read(self.address, self.size)

        # Join bytes (if 2 bytes): Unsigned
        reg = 0
        for byte in data:
            reg = (reg << 8) | byte
        # Mask field
        data = (reg & self.mask) >> self.lowest_bit

        # Apply sign extension if needed
        return self._convert_signed_unsigned(data, self.num_bits) if self.signed else data

    def __set__(self, obj: I2CDeviceDriver, value: int) -> None:
        if self.signed:
            value = self._convert_signed_unsigned(value, self.num_bits, unsigned_to_signed=False)

        data = obj.i2c_device.read(self.address, self.size)

        # Join bytes (if 2 bytes): Unsigned
        reg = 0
        for byte in data:
            reg = (reg << 8) | byte

        reg &= ~self.mask
        reg |= value << self.lowest_bit

        data = list(reg.to_bytes(self.size, "big"))
        obj.i2c_device.write(self.address, data)

    @staticmethod
    def _convert_signed_unsigned(value: int, num_bits: int, unsigned_to_signed: bool = True) -> int:
        bit_limit = 1 << num_bits

        if unsigned_to_signed and not (0 <= value < bit_limit):
            raise ValueError(f"Value {value} out of range for unsigned {num_bits}-bit integer")
        if not unsigned_to_signed and not (-(bit_limit // 2) <= value < bit_limit // 2):
            raise ValueError(f"Value {value} out of range for signed {num_bits}-bit integer")
        sign_bit = 1 << (num_bits - 1)
        return (value ^ sign_bit) - sign_bit if unsigned_to_signed else (value + sign_bit) ^ sign_bit


class RWRegister:
    """
    Read-Write register.

    This class provides a way to read and write integer values to a register of an I2C device.
    It is used as a descriptor to access the register value from an instance of a class that
    includes an I2C device interface.

    Attributes
    ----------
    address : int
        The register address to read/write.
    format : str
        The :py:class:`struct` format string for the register value.
    size : int
        The size of the register in bytes.

    Methods
    -------
    __get__(obj: I2CDeviceDriver, objtype: Optional[Type[I2CDeviceDriver]] = None) -> int
        Read the current value from the register.
    __set__(obj: I2CDeviceDriver, value: int) -> None
        Write a value to the register.

    See Also
    --------
    :class:`RORegister`
    """

    def __init__(self, register_address: int, struct_format: str) -> None:
        """
        Initialize the read-write register descriptor.

        Parameters
        ----------
        register_address : int
            The register address to read/write.
        struct_format : str
            The :py:class:`struct` format string for the register value.
        """
        self.address = register_address
        self.format = struct_format
        self.size = struct.calcsize(struct_format)

    def __get__(self, obj: I2CDeviceDriver, objtype: Optional[Type[I2CDeviceDriver]] = None) -> int:
        """
        Read the current value from the register.

        Parameters
        ----------
        obj : I2CDeviceDriver
            Instance containing the ``i2c_device`` for communication.
        objtype : Optional[Type[I2CDeviceDriver]], optional
            The type of the ``obj`` instance.

        Returns
        -------
        int
            Current value of the register.
        """
        data = obj.i2c_device.read(self.address, self.size)
        return struct.unpack(self.format, data)[0]

    def __set__(self, obj: I2CDeviceDriver, value: int) -> None:
        """
        Write a value to the register.

        Parameters
        ----------
        obj : I2CDeviceDriver
            Instance containing the ``i2c_device`` for communication.
        value : int
            Value to write to the register.
        """
        data = struct.pack(self.format, value)
        obj.i2c_device.write(self.address, data)


class RORegister(RWRegister):
    """
    Read-Only register.

    This class inherits from :class:`RWRegister` but does not allow writing.
    It is used to define registers that are read-only, such as status or
    configuration registers.

    Attributes
    ----------
    address : int
        The register address to read/write.
    format : str
        The :py:class:`struct` format string for the register value.
    size : int
        The size of the register in bytes.

    See Also
    --------
    :class:`RWRegister`
    """

    def __set__(self, obj: I2CDeviceDriver, value: int) -> NoReturn:
        """
        Prevent writing to a read-only register.

        Parameters
        ----------
        obj : I2CDeviceDriver
            Instance containing the ``i2c_device`` for communication.
        value : int
            Value attempted to be written.

        Raises
        ------
        :py:exc:`AttributeError`
            Always raised to indicate the register is read-only.
        """
        raise AttributeError("Cannot write to read-only register")


class RWBit:
    """
    Read-Write bit in a register.

    This class provides a way to read and write single bits in a register of an
    I2C device. It is used as a descriptor to access the bit value from an
    instance of a class that includes an I2C device interface.

    Attributes
    ----------
    address : int
        The register address to read/write.
    bit_mask : int
        Bit mask for the bit.
    byte : int
        The byte in the register containing the bit (1-2).

    Methods
    -------
    __get__(self, obj: I2CDeviceDriver, objtype: Optional[Type[I2CDeviceDriver]] = None) -> bool
        Read the current value of the bit.
    __set__(self, obj: I2CDeviceDriver, value: bool) -> None
        Write a value to the bit.

    See Also
    --------
    :class:`ROBit`
    """

    def __init__(self, register_address: int, bit: int, register_byte: int = 1) -> None:
        """
        Initialize the read-write bit descriptor.

        Parameters
        ----------
        register_address : int
            The register address to read/write.
        bit : int
            The position of the bit to read/write (0-based).
        register_byte : int, optional
            Size of the register in bytes, by default 1.

        Raises
        ------
        :py:exc:`ValueError`
            If ``bit`` is not between 0 and 7.
        :py:exc:`ValueError`
            If ``register_byte`` is not between 1 and 2.
        """
        if bit < 0 or bit > 7:
            raise ValueError("Bit must be between 0 and 7")
        if register_byte < 1 or register_byte > 2:
            raise ValueError("Register byte must be between 1 and 2")

        self.address = register_address
        self.bit_mask = 1 << bit
        self.byte = register_byte

    def __get__(self, obj: I2CDeviceDriver, objtype: Optional[Type[I2CDeviceDriver]] = None) -> bool:
        """
        Read the current value of the bit.

        Parameters
        ----------
        obj : I2CDeviceDriver
            Instance containing the ``i2c_device`` for communication.
        objtype : Optional[Type[I2CDeviceDriver]], optional
            The type of the ``obj`` instance.

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
            Instance containing the ``i2c_device`` for communication.
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

    This class provides a way to read a single bit in a register of an I2C device.
    It is used as a descriptor to access the bit value from an instance of a class
    that includes an I2C device interface.

    Attributes
    ----------
    address : int
        The register address to read/write.
    bit_mask : int
        Bit mask for the bit.
    byte : int
        The byte in the register containing the bit (1-2).
    bit : int
        The bit position in the byte (0-7).

    See Also
    --------
    :class:`RWBit`
    """

    def __set__(self, obj: I2CDeviceDriver, value: bool) -> NoReturn:
        """
        Prevent writing to a read-only bit.

        Parameters
        ----------
        obj : I2CDeviceDriver
            Instance containing the ``i2c_device`` for communication.
        value : bool
            Value attempted to be written.

        Raises
        ------
        :py:exc:`AttributeError`
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

    See Also
    --------
    :class:`ROBitsUnsigned`
    """

    def __init__(self, register_address: int, num_bits: int, lowest_bit: int, register_width: int = 1) -> None:
        """
        Initialize the read/write unsigned bit field descriptor.

        Parameters
        ----------
        register_address : int
            The register address to read/write.
        num_bits : int
            Number of bits in the bit field (must be positive).
        lowest_bit : int
            The position of the least significant bit (0-based).
        register_width : int, optional
            Size of the register in bytes, by default 1.

        Raises
        ------
        :py:exc:`ValueError`
            If ``num_bits`` is not positive.
        :py:exc:`ValueError`
            If ``lowest_bit`` is not non-negative.
        :py:exc:`ValueError`
            If ``register_width`` is not between 1 and 2.
        """
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
            Instance containing the ``i2c_device`` for communication.
        objtype : Optional[Type[I2CDeviceDriver]], optional
            The type of the ``obj`` instance.

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
            Instance containing the ``i2c_device`` for communication.
        value : int
            Value to write to the bits.

        Raises
        ------
        :py:exc:`ValueError`
            If ``value`` is out of range for the bit field.
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

    See Also
    --------
    :class:`RWBitsUnsigned`

    """

    def __set__(self, obj: I2CDeviceDriver, value: int) -> NoReturn:
        """
        Prevent writing to a read-only bit field.

        Parameters
        ----------
        obj : I2CDeviceDriver
            Instance containing the ``i2c_device`` for communication.
        value : int
            Value attempted to be written.

        Raises
        ------
        :py:exc:`AttributeError`
            Always raised to indicate the bit field is read-only.
        """
        raise AttributeError("Cannot write to read-only bit field")
