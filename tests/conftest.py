import sys
import types


class FakeBus:
    """Simulate an ``SMBus`` using a dictionary as memory."""

    def __init__(self, _busnum):
        self.memory = {
            (0x36, 0x00): 255,
            (0x36, 0x01): 255,
            (0x36, 0x02): 204,
            (0x36, 0x03): 96,
            (0x36, 0x04): 88,
            (0x36, 0x05): 17,
            (0x36, 0x06): 16,
            (0x36, 0x07): 0,
            (0x36, 0x08): 0,
            (0x36, 0x09): 18,
            (0x36, 0x0A): 128,
            (0x36, 0x0B): 48,
            (0x36, 0x0C): 151,
            (0x36, 0x0D): 28,
            (0x36, 0x0E): 255,
            (0x36, 0x0F): 255,
            (0x36, 0x10): 255,
            (0x36, 0x11): 255,
            (0x36, 0x12): 255,
            (0x36, 0x13): 255,
            (0x36, 0x14): 0,
            (0x36, 0x15): 255,
            (0x36, 0x16): 255,
            (0x36, 0x17): 253,
            (0x36, 0x18): 150,
            (0x36, 0x19): 12,
            (0x36, 0x1A): 1,
            (0x36, 0x1B): 255,
            (0x36, 0x1C): 255,
            (0x36, 0x1D): 255,
            (0x36, 0x1E): 255,
            (0x36, 0x1F): 255,
            (0x36, 0xFE): 255,
            (0x36, 0xFF): 255,
        }

    def read_i2c_block_data(self, address, register, length):
        """Read a block of data from memory."""
        return [self.memory.get((address, register + e), None) for e in range(length)]

    def write_i2c_block_data(self, address, register, data):
        """Write a block of data to memory."""
        for e in range(len(data)):
            self.memory[(address, register + e)] = data[e]

    def read_byte(self, address):
        """Read a byte from memory."""
        if address != 0x36:
            raise OSError("Device not found")
        return self.memory.get((address, 0), None)

    def close(self):
        pass


def pytest_configure():
    # The SMBus backend is unavailable in the test environment and is resolved
    # at import time. So a fixture would be applied too late.
    # Yeah. It's a global patch
    fake_loader = types.ModuleType("max1704x_smbus.smbus_loader")
    fake_loader.SMBus = FakeBus
    sys.modules["max1704x_smbus.smbus_loader"] = fake_loader


# If smbus_loader itself needs testing, isolate those tests in a separate
# directory so this global patch does not apply to them.
