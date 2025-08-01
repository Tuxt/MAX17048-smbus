# MAX17048-smbus

MAX17048/49 battery fuel gauge library using SMBus.

## Description

This library provides a Python interface to communicate with MAX17048/MAX17049 battery fuel gauge through SMBus/I²C. Specifically designed for Raspberry Pi and other Linux systems that support SMBus.

## Features

- Battery State of Charge (SoC) reading
- Battery voltage measurement
- Raspberry Pi compatible

## Installation

### Overview

This library requires one of several I²C backend libraries to communicate with hardware: `smbus`, `smbus2`, or `smbus3`. You can [install the library without a bankend](#install-the-library) if you already have one installed, [install a backend separately](#ic-backend-installation), or [install the library along with a backend](#install-with-an-optional-backend) in one step using optional dependencies.

### Install the library

To install the library without any backends (if you already have a backend installed or plan to install one manually):

```bash
pip install git+https://github.com/Tuxt/MAX17048-smbus.git
```

#### I²C backend installation

This library requires access to the I²C bus via one of the following compatible modules:

- [smbus3](https://pypi.org/project/smbus3/) — modern and actively maintained ([GitHub](https://github.com/eindiran/smbus3))
```bash
pip install smbus3
```

- [smbus2](https://pypi.org/project/smbus2/) — stable and widely used ([GitHub](https://github.com/kplindegaard/smbus2))
```bash
pip install smbus2
```

- [smbus](https://pypi.org/project/smbus/) — basic I²C support, limited features, commonly pre-installed on Raspberry Pi.
```bash
apt install python3-smbus   # preferred
# or
pip install smbus
```

### Install with an optional backend

Alternatively, you can install the library along with a backend in one step:

```bash
pip install git+https://github.com/Tuxt/MAX17048-smbus.git[smbus3]
# or
pip install git+https://github.com/Tuxt/MAX17048-smbus.git[smbus2]
# or
pip install git+https://github.com/Tuxt/MAX17048-smbus.git[smbus]
```

## Basic Usage

```python
from max1704x_smbus import MAX17048

# Create device instance
device = MAX17048()

# Read battery state and voltage
soc = device.state_of_charge  # %
voltage = device.voltage      # V
```

## Requirements

- Python ≥ 3.8
- Linux OS with SMBus support
- I²C/SMBus access (usually requires root permissions)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.