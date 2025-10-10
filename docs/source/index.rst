==============
MAX17048-smbus
==============

This Python library provides a simple interface for communicating with the MAX17048 (and likely compatible MAX17049) battery fuel gauge sensors over I²C.
Inspired by `Adafruit’s library`_, it uses ``smbus`` (with support for ``smbus2`` and ``smbus3``) instead of ``busio``, making it suitable for platforms such as the Raspberry Pi.
The library is lightweight and has no external dependencies beyond the I²C communication backend.

.. _Adafruit’s library: https://github.com/adafruit/Adafruit_CircuitPython_MAX1704x


.. toctree::
   :maxdepth: 1
   :caption: Getting Started

   install
   usage

.. toctree::
   :maxdepth: 1
   :caption: API Reference

   api/core_module
