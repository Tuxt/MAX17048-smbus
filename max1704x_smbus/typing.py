"""Protocol definitions used for static type checking."""

from typing import Protocol

from .i2c_device import I2CDevice


class I2CDeviceDriver(Protocol):
    """
    Describes classes that are drivers utilizing `I2CDevice`.

    Attributes
    ----------
    i2c_device : I2CDevice
        Underlying I2C communication interface.
    """

    i2c_device: I2CDevice
