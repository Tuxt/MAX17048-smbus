import importlib.util
import sys
import types

import pytest


# Inject a fake smbus backend
@pytest.fixture(autouse=True)
def fake_smbus_backend(monkeypatch, fake_bus):
    monkeypatch.setattr(importlib.util, "find_spec", lambda name: True if name == "smbus" else None)

    # Inject a module called smbus on sys.modules
    fake_mod = types.SimpleNamespace(SMBus=lambda busnum: fake_bus)
    monkeypatch.setitem(sys.modules, "smbus", fake_mod)


class FakeBus:
    """Simulate an ``SMBus`` using a dictionary as memory."""

    def __init__(self):
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


@pytest.fixture
def fake_bus():
    return FakeBus()


# Prepare the I2CDevice so you don't have to repeat the code in each test
@pytest.fixture
def i2c_device(fake_bus, monkeypatch):
    monkeypatch.setattr("max1704x_smbus.i2c_device.SMBus", lambda bus: fake_bus)
    from max1704x_smbus.i2c_device import I2CDevice

    return I2CDevice(1, 0x36)
