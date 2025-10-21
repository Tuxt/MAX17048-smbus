===================
max1704x_smbus.core
===================

.. module:: max1704x_smbus.core

This module provides the main public interface for interacting with the
MAX17048/MAX17049 fuel gauge devices. It contains the primary class
:py:class:`MAX17048` and several useful constants.


.. autodocstringclass:: max1704x_smbus.core.MAX17048
   :members:
   :special-members: __init__
   :no-docstring-members:


Module constants
----------------

.. autodata:: max1704x_smbus.core.ALERTFLAG_SOC_CHANGE
   :annotation: =0x20
.. autodata:: max1704x_smbus.core.ALERTFLAG_SOC_LOW
   :annotation: =0x10
.. autodata:: max1704x_smbus.core.ALERTFLAG_VOLTAGE_RESET
   :annotation: =0x08
.. autodata:: max1704x_smbus.core.ALERTFLAG_VOLTAGE_LOW
   :annotation: =0x04
.. autodata:: max1704x_smbus.core.ALERTFLAG_VOLTAGE_HIGH
   :annotation: =0x02
.. autodata:: max1704x_smbus.core.ALERTFLAG_RESET_INDICATOR
   :annotation: =0x01
