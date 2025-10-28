# MAX17048-smbus

A lightweight Python library for communicating with **MAX17048** (and likely compatible **MAX17049**) battery fuel gauge sensors over the **I²C/SMBus** interface.

This package provides a simple and dependency-minimal interface designed for environments like **Raspberry Pi** or other Linux-based systems with native SMBus support.

## Overview

`MAX17048-smbus` provides a straightforward and lightweight way to communicate with the MAX17048/MAX17049 battery fuel gauge sensors over SMBus/I²C.
It is especially suited for Raspberry Pi and other Linux systems with native SMBus support.

This library is designed to work **directly with standard SMBus backends** (`smbus`, `smbus2`, or `smbus3`), automatically selecting the first available one.

It aims to remain **minimal**, **easy to integrate**, and **dependency-minimal** across typical Linux environments, making it ideal for embedded systems like **Raspberry Pi**, **Orange Pi**, or other Linux-based boards.

## Features

- Read battery **State of Charge (SoC)**, **voltage**, and **charge/discharge rate**  
- Access **alert status** and configure **alert thresholds**
- Control **sleep** and **hibernation** modes
- Read and reset **configuration registers**
- Support for **MAX17048** (and likely compatible **MAX17049**) devices
- Works with `smbus`, `smbus2`, or `smbus3` backends (auto-detected)
- Designed for **Raspberry Pi** and other **Linux-based** systems
- **No external dependencies** beyond the SMBus backend

## Installation

### Basic installation

Install the library directly from PyPI:

```bash
pip install MAX17048-smbus
```
This install only the core library, assuming you already have an SMBus-compatible backend available on your system (such as `smbus`, `smbus2`, or `smbus3`).

On most **Raspberry Pi** systems, the `smbus` package is already available via APT:

```bash
sudo apt install python3-smbus
```

### With optional backend

If you don’t have any SMBus backend installed, you can install one together with the library:

```bash
pip install MAX17048-smbus[smbus3]
# or
pip install MAX17048-smbus[smbus2]
# or
pip install MAX17048-smbus[smbus]
```

Only one backend is needed — the library will automatically detect and use whichever is available.

## Quick Example

A minimal example showing how to read the battery state of charge and voltage:

```python
from max1704x_smbus import MAX17048

# Create device instance
device = MAX17048()

# Read battery information
soc = device.cell_percent       # %
voltage = device.cell_voltage   # V

print(f"SoC: {soc:.2f}% | Voltage: {voltage:.3f} V")
```

For more detailed usage examples, configuration options, and advanced features, see the [documentation on Read the Docs](https://max17048-smbus.readthedocs.io).

## Documentation

Comprehensive documentation is available online, including full API reference, configuration details, and usage examples:

👉 [https://max17048-smbus.readthedocs.io](https://max17048-smbus.readthedocs.io)

## Requirements

- Python **3.8** or newer  
- One of the following SMBus-compatible backends:
  - `smbus` | `python3-smbus`
  - `smbus2`
  - `smbus3`
- An I²C-capable system (e.g. Raspberry Pi, or any Linux board with `/dev/i2c-*` support)

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## Acknowledgements

This library was inspired by [Adafruit_CircuitPython_MAX1704x](https://github.com/adafruit/Adafruit_CircuitPython_MAX1704x), but was reimplemented from scratch to work with smbus/smbus2/smbus3 backends without external dependencies.

## Disclaimer

This library was inspired by [Adafruit_CircuitPython_MAX1704x](https://github.com/adafruit/Adafruit_CircuitPython_MAX1704x) but was **written from scratch** and is **not API-compatible** with it.

Support for the **MAX17049** device is **theoretical** — it has **not been tested**, though it is expected to work due to its register-level compatibility with the MAX17048.

This software is provided **“as is”**, without warranty of any kind, express or implied.
