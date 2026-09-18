from max1704x_smbus.i2c_device import I2CDevice


def test_read():
    i2c_device = I2CDevice(1, 0x36)
    assert i2c_device.read(0x02) == [204]


def test_write():
    i2c_device = I2CDevice(1, 0x36)
    i2c_device.write(0x02, [200])
    assert i2c_device.bus.memory[(0x36, 0x02)] == 200
