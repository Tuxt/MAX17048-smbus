"""
Register fields of an I²C device.

Provides the :class:`RegisterField` class for representing device registers or
arbitrary subfields within them. A field can cover the entire 16-bit register,
a single byte, any group of bits, or just one bit. Helper functions
(:func:`RWRegister`, :func:`RORegister`, :func:`RWBit`, :func:`ROBit`) are
included for the most common cases.

Constants
---------
The following constants are provided for the ``used_bytes`` parameter:

- ``USED_BYTES_MSB``  (-1): Use only the most significant byte.
- ``USED_BYTES_BOTH`` (0):  Use both bytes (the full 16-bit register).
- ``USED_BYTES_LSB``  (1):  Use only the least significant byte.

Examples
--------
Create a read-write 16-bit register (unsigned):

>>> reg = RWRegister(0x0A, used_bytes=USED_BYTES_BOTH)
>>> # 0x0A: [OOOOOOOO] 0x0B [OOOOOOOO]

Create a read-only 8-bit register (signed) on the first byte:

>>> reg = RORegister(0x0A, used_bytes=USED_BYTES_MSB, signed=True)
>>> # 0x0A: [OOOOOOOO] 0x0B [--------]

Create a read-only status bit:

>>> flag = ROBit(0x04, bit=13)
>>> # 0x04: [--O-----] 0x05 [--------]

Create a 3-bit read-only field from bit 7 to bit 5 (signed):

>>> mode = RegisterField(0x0C, num_bits=3, lowest_bit=5, signed=True, read_only=True)
>>> # 0x0C: [--------] 0x0D [OOO-----]

All registers are interpreted as big-endian.
"""

from typing import Optional, Type

from .protocols import I2CDeviceDriver

# Constants for `used_bytes` parameter
USED_BYTES_MSB: int = -1
USED_BYTES_BOTH: int = 0
USED_BYTES_LSB: int = 1


class RegisterField:
    """
    Read-write field within a register.

    Represents a subfield inside a 16-bit device register accessed over I²C.
    Handles masking, shifting, and optional sign extension so that field values
    can be read and written directly as Python integers, without manual bit
    manipulation.

    Attributes
    ----------
    address : int
        I²C register address where the field is located.
    size : int
        Number of bytes required to access the field (1 or 2).
        Registers are always 16-bit, but some fields can be accessed using
        only one byte when appropriate.
    num_bits : int
        Number of bits used by the field.
    lowest_bit : int
        Position of the least significant bit of the field within the register.
    mask : int
        Bit mask used to isolate the field value inside the register.
    signed : bool
        Whether the field value is signed.
    read_only : bool
        Whether the field is read-only

    Methods
    -------
    __get__(obj: I2CDeviceDriver, objtype: Optional[Type[I2CDeviceDriver]] = None) -> int
        Read the field value from the register.
    __set__(obj: I2CDeviceDriver, value: int) -> None
        Write an integer value into the field.
    _convert_signed_unsigned(value: int, num_bits: int, unsigned_to_signed: bool = True) -> int
        Convert between signed and unsigned values in a ``num_bits``-bit field.
        (Private helper, not intended for public use.)
    """

    def __init__(
        self,
        register_address: int,
        num_bits: int,
        lowest_bit: int = 0,
        signed: bool = False,
        independent_bytes: bool = False,
        read_only: bool = False,
    ) -> None:
        """
        Initialize the read-write register field.

        Parameters
        ----------
        register_address : int
            I²C register address where the field is located.
        num_bits : int
            Number of bits used by the field.
        lowest_bit : int, optional
            Position of the least significant bit of the field within the register.
            Defaults to ``0``.
        signed : bool, optional
            Whether the field value is signed. Defaults to ``False``.
        independent_bytes : bool, optional
            If ``True``, the field can be accessed using only the individual byte
            that contains it, instead of always requiring a 2-byte transaction.
            Defaults to ``False``.
        read_only : bool, optional
            If ``True``, the field is read-only and any attempt to assign a value
            will raise an :py:exc:`AttributeError`. Defaults to ``False``.

        Raises
        ------
        :py:exc:`ValueError`
            If the register address is not even.
        :py:exc:`ValueError`
            If ``num_bits`` is not in the range 1-16.
        :py:exc:`ValueError`
            If ``lowest_bit`` is not in the range 0-15.
        :py:exc:`ValueError`
            If the field size (``lowest_bit + num_bits``) exceeds 16 bits.
        """
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
        self.read_only = read_only

    def __get__(self, obj: I2CDeviceDriver, objtype: Optional[Type[I2CDeviceDriver]] = None) -> int:
        """
        Read the current field value from the register.

        Parameters
        ----------
        obj : I2CDeviceDriver
            Instance containing the ``i2c_device`` for communication.
        objtype : Optional[Type[I2CDeviceDriver]], optional
            The type of the ``obj`` instance.

        Returns
        -------
        int
            Value of the field extracted from the register.
        """
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
        """
        Write a value to the field within the register.

        Parameters
        ----------
        obj : I2CDeviceDriver
            Instance containing the ``i2c_device`` for communication.
        value : int
            Field value to write into the register.

        Raises
        ------
        :py:exc:`AttributeError`
            If attempting to write to a read-only register field.
        """
        if self.read_only:
            raise AttributeError("Cannot write to read-only register field")
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
        """
        Convert an integer between signed and unsigned representations.

        This helper interprets a limited-width integer either as signed
        or unsigned, depending on the ``unsigned_to_signed`` param. It can
        be used to reinterpret raw register values or to encode signed
        values for transmission.

        Parameters
        ----------
        value : int
            Integer value to convert.
        num_bits : int
            Number of valid bits in the value (bit width).
        unsigned_to_signed : bool, optional
            If True (default), interprets the unsigned input as signed.
            If False, converts a signed input to its unsigned representation.

        Returns
        -------
        int
            Converted integer in the requested representation.

        Raises
        ------
        :py:exc:`ValueError`
            If the value is out of range for the specified bit width.
        """
        bit_limit = 1 << num_bits

        if unsigned_to_signed and not (0 <= value < bit_limit):
            raise ValueError(f"Value {value} out of range for unsigned {num_bits}-bit integer")
        if not unsigned_to_signed and not (-(bit_limit // 2) <= value < bit_limit // 2):
            raise ValueError(f"Value {value} out of range for signed {num_bits}-bit integer")
        sign_bit = 1 << (num_bits - 1)
        return (value ^ sign_bit) - sign_bit if unsigned_to_signed else (value + sign_bit) ^ sign_bit


def RWRegister(  # noqa: N802
    register_address: int, used_bytes: int, signed: bool = False, independent_bytes: bool = False
) -> RegisterField:
    """
    Create a read-write register field representing one or two bytes.

    Parameters
    ----------
    register_address : int
        The register address to read from or write to.
    used_bytes : int
        Which byte(s) of the register to access:
        - ``USED_BYTES_MSB``  (-1): Use only the most significant byte (first byte)
        - ``USED_BYTES_BOTH`` (0):  Use both bytes (the full 16-bit register).
        - ``USED_BYTES_LSB``  (1):  Use only the least significant byte (second byte).
    signed : bool, optional
        Whether the register should be interpreted as signed.
        Defaults to ``False``.
    independent_bytes : bool, optional
        If ``True``, the register can be accessed using only the
        individual byte that contains it, instead of always
        requiring access to the full 16-bit register.
        Defaults to ``False``.

    Returns
    -------
    RegisterField
        A new ``RegisterField`` instance.

    See Also
    --------
    :class:`RegisterField`

    Notes
    -----
    All registers are assumed to use big-endian ordering:
    the first byte is the MSB and the second byte is the LSB.
    """
    return RegisterField(
        register_address,
        num_bits=16 - 8 * abs(used_bytes),
        lowest_bit=8 * (used_bytes == -1),
        signed=signed,
        independent_bytes=independent_bytes,
        read_only=False,
    )


def RORegister(  # noqa: N802
    register_address: int, used_bytes: int, signed: bool = False, independent_bytes: bool = False
) -> RegisterField:
    """
    Create a read-only register field representing one or two bytes.

    Parameters
    ----------
    register_address : int
        The register address to read from.
    used_bytes : int
        Which byte(s) of the register to access:
        - ``USED_BYTES_MSB``  (-1): Use only the most significant byte (first byte)
        - ``USED_BYTES_BOTH`` (0):  Use both bytes (the full 16-bit register).
        - ``USED_BYTES_LSB``  (1):  Use only the least significant byte (second byte).
    signed : bool, optional
        Whether the register should be interpreted as signed.
        Defaults to ``False``.
    independent_bytes : bool, optional
        If ``True``, the register can be accessed using only the
        individual byte that contains it, instead of always
        requiring access to the full 16-bit register.
        Defaults to ``False``.

    Returns
    -------
    RegisterField
        A new ``RegisterField`` instance.

    See Also
    --------
    :class:`RegisterField`

    Notes
    -----
    All registers are assumed to use big-endian ordering:
    the first byte is the MSB and the second byte is the LSB.
    """
    return RegisterField(
        register_address,
        num_bits=16 - 8 * abs(used_bytes),
        lowest_bit=8 * (used_bytes == -1),
        signed=signed,
        independent_bytes=independent_bytes,
        read_only=True,
    )


def RWBit(register_address: int, bit: int, independent_bytes: bool = False) -> RegisterField:  # noqa: N802
    """
    Create a read-write register field representing a single bit.

    Parameters
    ----------
    register_address : int
        The register address to read from or write to.
    bit : int
        Which bit of the register to access.
    independent_bytes : bool, optional
        If ``True``, the register can be accessed using only the
        individual byte that contains it, instead of always
        requiring access to the full 16-bit register.
        Defaults to ``False``.

    Returns
    -------
    RegisterField
        A new ``RegisterField`` instance.

    See Also
    --------
    :class:`RegisterField`

    Notes
    -----
    All registers are assumed to use big-endian ordering.
    """
    return RegisterField(
        register_address, num_bits=1, lowest_bit=bit, independent_bytes=independent_bytes, read_only=False
    )


def ROBit(register_address: int, bit: int, independent_bytes: bool = False) -> RegisterField:  # noqa: N802
    """
    Create a read-only register field representing a single bit.

    Parameters
    ----------
    register_address : int
        The register address to read from.
    bit : int
        Which bit of the register to access.
    independent_bytes : bool, optional
        If ``True``, the register can be accessed using only the
        individual byte that contains it, instead of always
        requiring access to the full 16-bit register.
        Defaults to ``False``.

    Returns
    -------
    RegisterField
        A new ``RegisterField`` instance.

    See Also
    --------
    :class:`RegisterField`

    Notes
    -----
    All registers are assumed to use big-endian ordering.
    """
    return RegisterField(
        register_address, num_bits=1, lowest_bit=bit, independent_bytes=independent_bytes, read_only=True
    )
