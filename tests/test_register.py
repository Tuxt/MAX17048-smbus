import re

import pytest
from max1704x_smbus.register import (
    USED_BYTES_BOTH,
    USED_BYTES_LSB,
    USED_BYTES_MSB,
    RegisterField,
    ROBit,
    RORegister,
    RWBit,
    RWRegister,
)


def make_dummy(i2c_device, register_field):
    class DummyDriver:
        def __init__(self, i2c_device):
            self.i2c_device = i2c_device
            self.address = register_field.address

        register = register_field

    return DummyDriver(i2c_device)


# fmt: off
correct_rw_cases = [
    # Full Register Unsigned
    (RWRegister(0x0A, used_bytes=USED_BYTES_BOTH), 0xFFFF, [0xFF, 0xFF]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_BOTH), 0x00FF, [0x00, 0xFF]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_BOTH), 0x0000, [0x00, 0x00]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_BOTH), 0xFF00, [0xFF, 0x00]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_BOTH), 0x0001, [0x00, 0x01]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_BOTH), 0x0080, [0x00, 0x80]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_BOTH), 0x0100, [0x01, 0x00]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_BOTH), 0x8000, [0x80, 0x00]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_BOTH), 0x01FF, [0x01, 0xFF]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_BOTH), 0xFF80, [0xFF, 0x80]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_BOTH), 0xFF56, [0xFF, 0x56]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_BOTH), 0xFFA9, [0xFF, 0xA9]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_BOTH), 0x56FF, [0x56, 0xFF]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_BOTH), 0xA9FF, [0xA9, 0xFF]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_BOTH), 0x0056, [0x00, 0x56]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_BOTH), 0x00A9, [0x00, 0xA9]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_BOTH), 0x5600, [0x56, 0x00]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_BOTH), 0xA900, [0xA9, 0x00]),

    # Full Register Signed
    (RWRegister(0x0A, used_bytes=USED_BYTES_BOTH, signed=True), 0, [0x00, 0x00]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_BOTH, signed=True), -1, [0xFF, 0xFF]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_BOTH, signed=True), 255, [0x00, 0xFF]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_BOTH, signed=True), -256, [0xFF, 0x00]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_BOTH, signed=True), 1, [0x00, 0x01]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_BOTH, signed=True), 128, [0x00, 0x80]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_BOTH, signed=True), 256, [0x01, 0x00]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_BOTH, signed=True), -32768, [0x80, 0x00]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_BOTH, signed=True), 511, [0x01, 0xFF]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_BOTH, signed=True), -128, [0xFF, 0x80]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_BOTH, signed=True), -170, [0xFF, 0x56]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_BOTH, signed=True), -87, [0xFF, 0xA9]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_BOTH, signed=True), 22271, [0x56, 0xFF]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_BOTH, signed=True), -22017, [0xA9, 0xFF]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_BOTH, signed=True), 86, [0x00, 0x56]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_BOTH, signed=True), 169, [0x00, 0xA9]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_BOTH, signed=True), 22016, [0x56, 0x00]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_BOTH, signed=True), -22272, [0xA9, 0x00]),

    # MSB Unsigned
    (RWRegister(0x0A, used_bytes=USED_BYTES_MSB), 0x00, [0x00, 0x30]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_MSB), 0xFF, [0xFF, 0x30]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_MSB), 0x01, [0x01, 0x30]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_MSB), 0x80, [0x80, 0x30]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_MSB), 0x0F, [0x0F, 0x30]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_MSB), 0xF0, [0xF0, 0x30]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_MSB), 0x55, [0x55, 0x30]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_MSB), 0xAA, [0xAA, 0x30]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_MSB), 0x66, [0x66, 0x30]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_MSB), 0x99, [0x99, 0x30]),

    # MSB Signed
    (RWRegister(0x0A, used_bytes=USED_BYTES_MSB, signed=True), 0, [0x00, 0x30]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_MSB, signed=True), -1, [0xFF, 0x30]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_MSB, signed=True), 127, [0x7F, 0x30]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_MSB, signed=True), -2, [0xFE, 0x30]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_MSB, signed=True), -128, [0x80, 0x30]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_MSB, signed=True), 15, [0x0F, 0x30]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_MSB, signed=True), -16, [0xF0, 0x30]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_MSB, signed=True), 85, [0x55, 0x30]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_MSB, signed=True), -86, [0xAA, 0x30]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_MSB, signed=True), 102, [0x66, 0x30]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_MSB, signed=True), -103, [0x99, 0x30]),

    # LSB Unsigned
    (RWRegister(0x0A, used_bytes=USED_BYTES_LSB), 0x00, [0x80, 0x00]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_LSB), 0xFF, [0x80, 0xFF]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_LSB), 0x01, [0x80, 0x01]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_LSB), 0x80, [0x80, 0x80]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_LSB), 0x0F, [0x80, 0x0F]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_LSB), 0xF0, [0x80, 0xF0]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_LSB), 0x55, [0x80, 0x55]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_LSB), 0xAA, [0x80, 0xAA]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_LSB), 0x66, [0x80, 0x66]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_LSB), 0x99, [0x80, 0x99]),

    # LSB Signed
    (RWRegister(0x0A, used_bytes=USED_BYTES_LSB, signed=True), 0, [0x80, 0x00]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_LSB, signed=True), -1, [0x80, 0xFF]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_LSB, signed=True), 127, [0x80, 0x7F]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_LSB, signed=True), -2, [0x80, 0xFE]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_LSB, signed=True), -128, [0x80, 0x80]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_LSB, signed=True), 15, [0x80, 0x0F]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_LSB, signed=True), -16, [0x80, 0xF0]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_LSB, signed=True), 85, [0x80, 0x55]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_LSB, signed=True), -86, [0x80, 0xAA]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_LSB, signed=True), 102, [0x80, 0x66]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_LSB, signed=True), -103, [0x80, 0x99]),

    # Bit on LSB
    (RWBit(0x0A, 0), 1, [0x80, 0x31]),
    (RWBit(0x0A, 0), 0, [0x80, 0x30]),
    (RWBit(0x0A, 1), 1, [0x80, 0x32]),
    (RWBit(0x0A, 1), 0, [0x80, 0x30]),
    (RWBit(0x0A, 6), 1, [0x80, 0x70]),
    (RWBit(0x0A, 6), 0, [0x80, 0x30]),
    (RWBit(0x0A, 7), 1, [0x80, 0xB0]),
    (RWBit(0x0A, 7), 0, [0x80, 0x30]),

    # Bit on MSB
    (RWBit(0x0A, 15), 1, [0x80, 0x30]),
    (RWBit(0x0A, 15), 0, [0x00, 0x30]),
    (RWBit(0x0A, 14), 1, [0xC0, 0x30]),
    (RWBit(0x0A, 14), 0, [0x80, 0x30]),
    (RWBit(0x0A,  9), 1, [0x82, 0x30]),
    (RWBit(0x0A,  9), 0, [0x80, 0x30]),
    (RWBit(0x0A,  8), 1, [0x81, 0x30]),
    (RWBit(0x0A,  8), 0, [0x80, 0x30]),
    
    # Bit group MSB Unsigned
    (RegisterField(0x14, num_bits=3, lowest_bit=11), 0x07, [0x38, 0xFF]),
    (RegisterField(0x14, num_bits=3, lowest_bit=11), 0x00, [0x00, 0xFF]),
    (RegisterField(0x14, num_bits=5, lowest_bit=11), 0x0B, [0x58, 0xFF]),
    (RegisterField(0x14, num_bits=5, lowest_bit=11), 0x00, [0x00, 0xFF]),
    (RegisterField(0x14, num_bits=2, lowest_bit=14), 2, [0x80, 0xFF]),
    (RegisterField(0x14, num_bits=2, lowest_bit=14), 0, [0x00, 0xFF]),

    # Bit group MSB Signed
    (RegisterField(0x14, num_bits=3, lowest_bit=11, signed=True), -1, [0x38, 0xFF]),
    (RegisterField(0x14, num_bits=3, lowest_bit=11, signed=True),  0, [0x00, 0xFF]),
    (RegisterField(0x14, num_bits=5, lowest_bit=11, signed=True), 11, [0x58, 0xFF]),
    (RegisterField(0x14, num_bits=5, lowest_bit=11, signed=True),  0, [0x00, 0xFF]),
    (RegisterField(0x14, num_bits=2, lowest_bit=14, signed=True), -1, [0xC0, 0xFF]),
    (RegisterField(0x14, num_bits=2, lowest_bit=14, signed=True), 0, [0x00, 0xFF]),

    # Bit group LSB Unsigned
    (RegisterField(0x14, num_bits=4, lowest_bit=3), 0x0F, [0x00, 0xFF]),
    (RegisterField(0x14, num_bits=4, lowest_bit=3), 0x00, [0x00, 0x87]),
    (RegisterField(0x14, num_bits=6, lowest_bit=0), 0x2E, [0x00, 0xEE]),
    (RegisterField(0x14, num_bits=6, lowest_bit=0), 0x00, [0x00, 0xC0]),
    (RegisterField(0x14, num_bits=2, lowest_bit=6), 0x02, [0x00, 0xBF]),
    (RegisterField(0x14, num_bits=2, lowest_bit=6), 0x00, [0x00, 0x3F]),

    # Bit group LSB Signed
    (RegisterField(0x14, num_bits=4, lowest_bit=3, signed=True), -7, [0x00, 0xCF]),
    (RegisterField(0x14, num_bits=4, lowest_bit=3, signed=True),  0, [0x00, 0x87]),
    (RegisterField(0x14, num_bits=6, lowest_bit=0, signed=True), 27, [0x00, 0xDB]),
    (RegisterField(0x14, num_bits=6, lowest_bit=0, signed=True), -13, [0x00, 0xF3]),
    (RegisterField(0x14, num_bits=2, lowest_bit=6, signed=True), -2, [0x00, 0xBF]),
    (RegisterField(0x14, num_bits=2, lowest_bit=6, signed=True), 1, [0x00, 0x7F]),

    # Bit group cross-byte Unsigned
    (RegisterField(0x14, num_bits=6, lowest_bit=6), 0x3F, [0x0F, 0xFF]),
    (RegisterField(0x14, num_bits=6, lowest_bit=6), 0x00, [0x00, 0x3F]),
    (RegisterField(0x14, num_bits=6, lowest_bit=6), 0x27, [0x09, 0xFF]),
    (RegisterField(0x14, num_bits=6, lowest_bit=6), 0x2A, [0x0A, 0xBF]),
    (RegisterField(0x14, num_bits=6, lowest_bit=6), 0x15, [0x05, 0x7F]),
    (RegisterField(0x14, num_bits=10, lowest_bit=0), 0x3FF, [0x03, 0xFF]),
    (RegisterField(0x14, num_bits=10, lowest_bit=0), 0x000, [0x00, 0x00]),
    (RegisterField(0x14, num_bits=10, lowest_bit=0), 0x3C5, [0x03, 0xC5]),
    (RegisterField(0x14, num_bits=10, lowest_bit=0), 0x005, [0x00, 0x05]),
    (RegisterField(0x14, num_bits=9, lowest_bit=7), 0x1FF, [0xFF, 0xFF]),
    (RegisterField(0x14, num_bits=9, lowest_bit=7), 0x000, [0x00, 0x7F]),
    (RegisterField(0x14, num_bits=9, lowest_bit=7), 0xAA, [0x55, 0x7F]),
    (RegisterField(0x14, num_bits=9, lowest_bit=7), 0x155, [0xAA, 0xFF]),

    # Bit group cross-byte Signed
    (RegisterField(0x14, num_bits=6, lowest_bit=6, signed=True), -1, [0x0F, 0xFF]),
    (RegisterField(0x14, num_bits=6, lowest_bit=6, signed=True), 0, [0x00, 0x3F]),
    (RegisterField(0x14, num_bits=6, lowest_bit=6, signed=True), -25, [0x09, 0xFF]),
    (RegisterField(0x14, num_bits=6, lowest_bit=6, signed=True), -22, [0x0A, 0xBF]),
    (RegisterField(0x14, num_bits=6, lowest_bit=6, signed=True), 21, [0x05, 0x7F]),
    (RegisterField(0x14, num_bits=10, lowest_bit=0, signed=True), -1, [0x03, 0xFF]),
    (RegisterField(0x14, num_bits=10, lowest_bit=0, signed=True), 0, [0x00, 0x00]),
    (RegisterField(0x14, num_bits=10, lowest_bit=0, signed=True), -400, [0x02, 0x70]),
    (RegisterField(0x14, num_bits=10, lowest_bit=0, signed=True), 294, [0x01, 0x26]),
    (RegisterField(0x14, num_bits=9, lowest_bit=7, signed=True), -1, [0xFF, 0xFF]),
    (RegisterField(0x14, num_bits=9, lowest_bit=7, signed=True), 0, [0x00, 0x7F]),
    (RegisterField(0x14, num_bits=9, lowest_bit=7, signed=True), 170, [0x55, 0x7F]),
    (RegisterField(0x14, num_bits=9, lowest_bit=7, signed=True), -171, [0xAA, 0xFF]),

    # Independent bytes
    (RWRegister(0x0A, used_bytes=USED_BYTES_MSB, independent_bytes=True), 0x00, [0x00, 0x30]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_LSB, independent_bytes=True), 0x00, [0x00, 0x97]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_MSB, independent_bytes=True), 0xFF, [0xFF, 0x30]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_LSB, independent_bytes=True), 0xFF, [0xFF, 0x97]),
    (RWBit(0x0A, 0, independent_bytes=True), 0, [0x30, 0x97]),
    (RWBit(0x0A, 0, independent_bytes=True), 1, [0x31, 0x97]),
    (RWBit(0x0A, 15, independent_bytes=True), 0, [0x00, 0x30]),
    (RWBit(0x0A, 15, independent_bytes=True), 1, [0x80, 0x30]),
]

incorrect_write_cases = [
    # Write on read-only
    (RORegister(0x0A, used_bytes=USED_BYTES_BOTH), 0x00, AttributeError, "Cannot write to read-only register field", [0x80, 0x30]),
    (RORegister(0x0A, used_bytes=USED_BYTES_LSB, signed=True), 0x32, AttributeError, "Cannot write to read-only register field", [0x80, 0x30]),
    (RORegister(0x0A, used_bytes=USED_BYTES_MSB), 0xFF00, AttributeError, "Cannot write to read-only register field", [0x80, 0x30]),
    (ROBit(0x0A, 12), 1, AttributeError, "Cannot write to read-only register field", [0x80, 0x30]),
    (ROBit(0x0A, 7), 0, AttributeError, "Cannot write to read-only register field", [0x80, 0x30]),
    (ROBit(0x0A, 0), 1, AttributeError, "Cannot write to read-only register field", [0x80, 0x30]),
    (RegisterField(0x14, num_bits=3, lowest_bit=11, read_only=True), 0x07, AttributeError, "Cannot write to read-only register field", [0x00, 0xFF]),
    (RegisterField(0x14, num_bits=10, lowest_bit=3, read_only=True), 0x2B, AttributeError, "Cannot write to read-only register field", [0x00, 0xFF]),
    
    # Write out of bound Unsigned
    (RWRegister(0x0A, used_bytes=USED_BYTES_BOTH), 0x1FFFF, OverflowError, f"Value {0x1FFFF} out of range for unsigned 16-bit integer", [0x80, 0x30]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_LSB), 0x1FF, OverflowError, f"Value {0x1FF} out of range for unsigned 8-bit integer", [0x80, 0x30]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_MSB), 0x1FF, OverflowError, f"Value {0x1FF} out of range for unsigned 8-bit integer", [0x80, 0x30]),
    (RWBit(0x0A, 4), 2, OverflowError, "Value 2 out of range for unsigned 1-bit integer", [0x80, 0x30]),
    (RWBit(0x0A, 15), -3, OverflowError, "Value -3 out of range for unsigned 1-bit integer", [0x80, 0x30]),
    (RegisterField(0x0A, num_bits=4, lowest_bit=1), 0x10, OverflowError, f"Value {0x10} out of range for unsigned 4-bit integer", [0x80, 0x30]),
    (RegisterField(0x0A, num_bits=9, lowest_bit=0), 0x400, OverflowError, f"Value {0x400} out of range for unsigned 9-bit integer", [0x80, 0x30]),
    (RegisterField(0x0A, num_bits=6, lowest_bit=10), 0x40, OverflowError, f"Value {0x40} out of range for unsigned 6-bit integer", [0x80, 0x30]),
    
    # Write out of bound Signed
    (RWRegister(0x0A, used_bytes=USED_BYTES_BOTH, signed=True), 0x8000, OverflowError, f"Value {0x8000} out of range for signed 16-bit integer", [0x80, 0x30]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_BOTH, signed=True), -0x8001, OverflowError, f"Value {-0x8001} out of range for signed 16-bit integer", [0x80, 0x30]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_BOTH, signed=True), 0x8FB3, OverflowError, f"Value {0x8FB3} out of range for signed 16-bit integer", [0x80, 0x30]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_BOTH, signed=True), -0x89C0, OverflowError, f"Value {-0x89C0} out of range for signed 16-bit integer", [0x80, 0x30]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_LSB, signed=True), 0x80, OverflowError, f"Value {0x80} out of range for signed 8-bit integer", [0x80, 0x30]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_MSB, signed=True), -0x81, OverflowError, f"Value {-0x81} out of range for signed 8-bit integer", [0x80, 0x30]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_LSB, signed=True), 0xC4, OverflowError, f"Value {0xC4} out of range for signed 8-bit integer", [0x80, 0x30]),
    (RWRegister(0x0A, used_bytes=USED_BYTES_MSB, signed=True), -0xC2, OverflowError, f"Value {-0xC2} out of range for signed 8-bit integer", [0x80, 0x30]),
    (RegisterField(0x0A, num_bits=4, lowest_bit=1, signed=True), 0x08, OverflowError, f"Value {0x08} out of range for signed 4-bit integer", [0x80, 0x30]),
    (RegisterField(0x0A, num_bits=4, lowest_bit=1, signed=True), -0x09, OverflowError, f"Value {-0x09} out of range for signed 4-bit integer", [0x80, 0x30]),
    (RegisterField(0x0A, num_bits=9, lowest_bit=0, signed=True), 0x100, OverflowError, f"Value {0x100} out of range for signed 9-bit integer", [0x80, 0x30]),
    (RegisterField(0x0A, num_bits=9, lowest_bit=0, signed=True), -0x101, OverflowError, f"Value {-0x101} out of range for signed 9-bit integer", [0x80, 0x30]),
    (RegisterField(0x0A, num_bits=6, lowest_bit=10, signed=True), 0x20, OverflowError, f"Value {0x20} out of range for signed 6-bit integer", [0x80, 0x30]),
    (RegisterField(0x0A, num_bits=6, lowest_bit=10, signed=True), -0x21, OverflowError, f"Value {-0x21} out of range for signed 6-bit integer", [0x80, 0x30]),
]

incorrect_instantiation_cases = [
    # Odd address
    (RegisterField, [0x0B, 2, 0], ValueError, f"Register address must be even, got {0x0B}"),
    (RegisterField, [0x01, 8, 8], ValueError, f"Register address must be even, got {0x01}"),
    (RWRegister, [0x0D, USED_BYTES_BOTH, True], ValueError, f"Register address must be even, got {0x0D}"),
    (RORegister, [0x0D, USED_BYTES_LSB], ValueError, f"Register address must be even, got {0x0D}"),
    (RWRegister, [0x0D, USED_BYTES_MSB], ValueError, f"Register address must be even, got {0x0D}"),
    (RWBit, [0x0F, 3], ValueError, f"Register address must be even, got {0x0F}"),
    (RWBit, [0x0B, 11], ValueError, f"Register address must be even, got {0x0B}"),

    # Invalid num_bits-lowest_bit combination
    (RegisterField, [0x0A, 0, 0], ValueError, "Invalid num_bits 0, must be in range 1-16"),
    (RegisterField, [0x0A, 17, 0], ValueError, "Invalid num_bits 17, must be in range 1-16"),
    (RegisterField, [0x0A, 1, -1], ValueError, "Invalid lowest_bit -1, must be in range 0-15"),
    (RegisterField, [0x0A, 2, 16], ValueError, "Invalid lowest_bit 16, must be in range 0-15"),
    (RegisterField, [0x0A, 8, 10], ValueError, "Invalid field size: lowest_bit (10) + num_bits (8) exceeds 16 bits"),

    # Invalid used_bytes (RWRegister|RORegister)
    (RWRegister, [0x0A, -2], ValueError, "Invalid num_bits 0, must be in range 1-16"),
    (RWRegister, [0x0A, 2], ValueError, "Invalid num_bits 0, must be in range 1-16"),

    # Invalid bit value (RWBit|ROBit)
    (RWBit, [0x0A, -1], ValueError, "Invalid lowest_bit -1, must be in range 0-15"),
    (RWBit, [0x0A, 16], ValueError, "Invalid lowest_bit 16, must be in range 0-15"),
]
# fmt: on


@pytest.mark.parametrize("register_field, write_val, expected_bytes", correct_rw_cases)
def test_rw(fake_bus, i2c_device, register_field, write_val, expected_bytes):
    driver = make_dummy(i2c_device, register_field)
    driver.register = write_val
    assert fake_bus.memory[(0x36, driver.address)] == expected_bytes[0]
    assert fake_bus.memory[(0x36, driver.address + 1)] == expected_bytes[1]
    assert driver.register == write_val


@pytest.mark.parametrize("register_field, write_val, error, message, expected_bytes", incorrect_write_cases)
def test_incorrect_write(fake_bus, i2c_device, register_field, write_val, error, message, expected_bytes):
    driver = make_dummy(i2c_device, register_field)
    with pytest.raises(error, match=message):
        driver.register = write_val
    assert fake_bus.memory[(0x36, driver.address)] == expected_bytes[0]
    assert fake_bus.memory[(0x36, driver.address + 1)] == expected_bytes[1]


@pytest.mark.parametrize("register_class, kwargs, error, message", incorrect_instantiation_cases)
def test_instanciation(fake_bus, i2c_device, register_class, kwargs, error, message):
    with pytest.raises(error, match=re.escape(message)):
        register_field = register_class(*kwargs)
