============
Installation
============

You can install this library using pip:

.. code-block:: bash

   pip install MAX17048-smbus

Alternatively, you can install it from source:

.. code-block:: bash

   git clone https://github.com/Tuxt/MAX17048-smbus.git
   cd MAX17048-smbus
   pip install .

| By default, this installs the library without any I²C backend.
| To communicate with the sensor, you must ensure that a supported backend is available:

* ``smbus3`` - see `smbus3 on PyPI <https://pypi.org/project/smbus3/>`_
* ``smbus2`` - see `smbus2 on PyPI <https://pypi.org/project/smbus2/>`_
* ``smbus`` - see `smbus on PyPI <https://pypi.org/project/smbus/>`_

You can install the library with a specific backend using pip extras:

.. code-block:: bash

   pip install MAX17048-smbus[smbus3]
   pip install MAX17048-smbus[smbus2]
   pip install MAX17048-smbus[smbus]

You can also install ``smbus`` using system packages:

.. code-block:: bash

   sudo apt install python3-smbus

If you're using a Raspberry Pi, make sure I²C is enabled.