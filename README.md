# MAX17048-smbus

MAX17048/49 battery fuel gauge library using SMBus.

## Description

This library provides a Python interface to communicate with MAX17048/MAX17049 battery fuel gauge through SMBus/I2C. Specifically designed for Raspberry Pi and other Linux systems that support SMBus.

## Features

- Battery State of Charge (SoC) reading
- Battery voltage measurement
- Raspberry Pi compatible

## Installation

Install directly from GitHub:
```bash
pip install git+https://github.com/Tuxt/MAX17048-smbus.git
```

For development:
```bash
git clone https://github.com/Tuxt/MAX17048-smbus.git
cd MAX17048-smbus
pip install -e .
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
- I2C/SMBus access (usually requires root permissions)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.