def test_read(fake_bus, i2c_device):
    assert i2c_device.read(0x02) == [204]


def test_write(fake_bus, i2c_device):
    i2c_device.write(0x02, [200])
    assert fake_bus.memory[(0x36, 0x02)] == 200
