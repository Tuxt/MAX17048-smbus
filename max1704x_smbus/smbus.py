"""
Automatically detects an available SMBus backend and exposes a unified interface.

This module detects and imports the first available SMBus-compatible
backend (`smbus3`, `smbus2`, or `smbus`), in order of preference, and
exposes a unified interface to be used throughout the codebase.

By isolating this logic, other parts of the library can access `SMBus`
without concern for which backend is actually available.

Exports:
    SMBus (class): The SMBus class from the selected backend.
    _BACKEND (str): Name of the backend selected ("smbus3", "smbus2", or "smbus").
    _USING_SMBUS23 (bool): True if the selected backend is `smbus2` or `smbus3`,
                           which share a mostly compatible API.
"""

from importlib.util import find_spec

if find_spec("smbus3") is not None:
    from smbus3 import SMBus

    _BACKEND = "smbus3"
    _USING_SMBUS23 = True
elif find_spec("smbus2") is not None:
    from smbus2 import SMBus

    _BACKEND = "smbus2"
    _USING_SMBUS23 = True
elif find_spec("smbus") is not None:
    from smbus import SMBus

    _BACKEND = "smbus"
    _USING_SMBUS23 = False
else:
    raise ModuleNotFoundError("No suitable SMBus library found. Please install 'smbus3', 'smbus2', or 'smbus1'.")

__all__ = ["_BACKEND", "_USING_SMBUS23", "SMBus"]
